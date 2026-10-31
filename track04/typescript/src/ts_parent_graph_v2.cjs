#!/usr/bin/env node
'use strict';
/**
 * TRACK04 G1.1 - deterministic parent-only TypeScript source-universe inventory.
 * Engineering diagnostic; NOT RM-CSS scoring, regeneration, or F2P/P2P.
 * --repo must be a frozen parent checkout. Never uses child patch/tests as input.
 * Pinned upstream TypeScript compiler is resolved from --repo/node_modules.
 */
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const cp = require('node:child_process');
const {createRequire} = require('node:module');

const PROD_SUFFIXES = ['.ts', '.tsx', '.mts', '.cts'];
const EXCLUDED_DIRS = new Set(['node_modules','test','tests','__tests__','e2e','integration','bench','benches','benchmarks','coverage','dist','build','out','generated','.git','.turbo','.cache']);
const EXCLUDED_FILE = /(?:^|\/)(?:[^/]+\.(?:spec|test|bench|d)\.[cm]?tsx?|[^/]+\.generated\.[cm]?tsx?)$/i;
const sha = text => crypto.createHash('sha256').update(text).digest('hex');
const relNorm = (base, file) => path.relative(base, file).split(path.sep).join('/');
const isWithin = (root, file) => file === root || file.startsWith(root + path.sep);

function parseArgs(argv) {
  const o = {};
  for (let i = 0; i < argv.length; i++) {
    const key = argv[i];
    if (!['--repo','--profile','--out','--expected-parent'].includes(key) || !argv[i+1] || argv[i+1].startsWith('--'))
      throw new Error('USAGE: --repo PATH --profile tinybench|nestjs [--out FILE] [--expected-parent SHA40]');
    o[key.substring(2)] = argv[++i];
  }
  if (!o.repo || !['tinybench','nestjs'].includes(o.profile)) throw new Error('REPO_PROFILE_REQUIRED');
  if (o['expected-parent'] && !/^[0-9a-f]{40}$/i.test(o['expected-parent'])) throw new Error('INVALID_PARENT_SHA');
  return o;
}

function allowedProductionFile(rel, profile) {
  const normalized = rel.replace(/\\/g,'/');
  const seg = normalized.split('/');
  if (seg.some(s=>EXCLUDED_DIRS.has(s))) return false;
  if (EXCLUDED_FILE.test(normalized)) return false;
  if (!PROD_SUFFIXES.some(s=>normalized.endsWith(s))) return false;
  if (profile === 'tinybench') return seg.length >= 2 && seg[0] === 'src';
  if (profile === 'nestjs') return seg.length >= 4 && seg[0] === 'packages' && seg[2] === 'src';
  return false;
}

function walk(root, profile) {
  const found=[];
  const visit=(dir)=>{
    for (const entry of fs.readdirSync(dir,{withFileTypes:true}).sort((a,b)=>a.name.localeCompare(b.name,'en'))) {
      const fp=path.join(dir,entry.name);
      if (entry.isSymbolicLink()) continue; // never follow symlink paths
      if (entry.isDirectory()) {
        if (!EXCLUDED_DIRS.has(entry.name)) visit(fp);
      } else if(entry.isFile()) {
        const rel=relNorm(root,fp);
        if (allowedProductionFile(rel,profile)) {
          if(!isWithin(root,fs.realpathSync(fp))) throw new Error('PATH_ESCAPE');
          found.push(fp);
        }
      }
    }
  };
  const first=profile==='tinybench'?[path.join(root,'src')]:[path.join(root,'packages')];
  for(const fp of first) if(fs.existsSync(fp)) visit(fp);
  return found.sort((a,b)=>relNorm(root,a).localeCompare(relNorm(root,b),'en'));
}

function loadTs(root) {
  try {return createRequire(path.join(root,'package.json'))('typescript');}
  catch(e) {
    if(process.env.TRACK04_TS_LOCAL_FALLBACK==='1') return require('typescript');
    throw new Error('PINNED_TYPESCRIPT_NOT_INSTALLED_IN_PARENT');
  }
}
function readCompilerOptions(ts,root) {
  const cfg=path.join(root,'tsconfig.json');
  if(!fs.existsSync(cfg)) throw new Error('TSCONFIG_MISSING');
  const j=ts.readConfigFile(cfg,ts.sys.readFile);
  if(j.error) throw new Error('TSCONFIG_READ_ERROR '+ts.flattenDiagnosticMessageText(j.error.messageText,' '));
  const parsed=ts.parseJsonConfigFileContent(j.config,ts.sys,root);
  if(parsed.errors.length) throw new Error('TSCONFIG_PARSE_ERROR '+parsed.errors.map(e=>ts.flattenDiagnosticMessageText(e.messageText,' ')).join(' '));
  return parsed.options;
}
function collectModuleSpecifiers(ts,node,into) {
  // Static import/export (including export * and type-only imports).
  if ((ts.isImportDeclaration(node) || ts.isExportDeclaration(node)) && node.moduleSpecifier && ts.isStringLiteralLike(node.moduleSpecifier)) {
    into.add(node.moduleSpecifier.text);
  }
  // import x = require('x')
  if(ts.isImportEqualsDeclaration(node) && ts.isExternalModuleReference(node.moduleReference) && node.moduleReference.expression && ts.isStringLiteralLike(node.moduleReference.expression)) {
    into.add(node.moduleReference.expression.text);
  }
  // require('x') and import('x') with a literal only, never execute.
  if(ts.isCallExpression(node) && node.arguments.length===1 && ts.isStringLiteralLike(node.arguments[0])) {
    if ((ts.isIdentifier(node.expression) && node.expression.text === 'require') || node.expression.kind===ts.SyntaxKind.ImportKeyword)
      into.add(node.arguments[0].text);
  }
  ts.forEachChild(node, n=>collectModuleSpecifiers(ts,n,into));
}
function pushUnit(ts, sf, node, kind, name, units, fullText) {
  const start=node.getStart(sf,false),end=node.end;
  const raw=fullText.slice(start,end);
  const startLine=sf.getLineAndCharacterOfPosition(start).line+1;
  const endLine=sf.getLineAndCharacterOfPosition(end).line+1;
  units.push({kind,name,start_line:startLine,end_line:endLine,start_offset_utf16:start,end_offset_utf16:end,sha256:sha(raw)});
}
function collectUnits(ts,sf,fullText) {
  const units=[];
  const nameOf=n=>n.name&&n.name.getText(sf)||'<anonymous>';
  for (const n of sf.statements) {
    if(ts.isFunctionDeclaration(n)) {
      pushUnit(ts,sf,n,'function',nameOf(n),units,fullText);
    } else if(ts.isClassDeclaration(n)) {
      pushUnit(ts,sf,n,'class',nameOf(n),units,fullText);
      for(const m of n.members) {
        if(ts.isMethodDeclaration(m)||ts.isConstructorDeclaration(m)||ts.isGetAccessorDeclaration(m)||ts.isSetAccessorDeclaration(m))
          pushUnit(ts,sf,m,'method',nameOf(m),units,fullText);
      }
    } else if(ts.isInterfaceDeclaration(n)) {
      pushUnit(ts,sf,n,'interface',nameOf(n),units,fullText);
    } else if(ts.isTypeAliasDeclaration(n)) {
      pushUnit(ts,sf,n,'type_alias',nameOf(n),units,fullText);
    } else if(ts.isEnumDeclaration(n)) {
      pushUnit(ts,sf,n,'enum',nameOf(n),units,fullText);
    } else if(ts.isModuleDeclaration(n)) {
      pushUnit(ts,sf,n,'namespace',nameOf(n),units,fullText);
    } else if(ts.isVariableStatement(n)) {
      for(const d of n.declarationList.declarations) {
        const init=d.initializer;
        const kind=init && (ts.isArrowFunction(init)||ts.isFunctionExpression(init))
          ? 'function_expression' : 'variable_declaration';
        pushUnit(ts,sf,d,kind,nameOf(d),units,fullText);
      }
    } else if(ts.isExportDeclaration(n)) {
      const label=n.moduleSpecifier && ts.isStringLiteralLike(n.moduleSpecifier)
        ? n.moduleSpecifier.text : '<local>';
      pushUnit(ts,sf,n,'export_declaration',label,units,fullText);
    } else if(ts.isExportAssignment(n)) {
      pushUnit(ts,sf,n,'export_assignment','default',units,fullText);
    } else if(ts.isImportEqualsDeclaration(n)) {
      pushUnit(ts,sf,n,'import_alias',nameOf(n),units,fullText);
    }
  }
  // Make non-indexable files visible, never silently drop them from an index.
  if(!units.length) {
    units.push({kind:'module_fallback',name:'<whole-file>',start_line:1,
      end_line:sf.getLineAndCharacterOfPosition(fullText.length).line+1,
      start_offset_utf16:0,end_offset_utf16:fullText.length,sha256:sha(fullText)});
  }
  return units;
}

function verifyParent(root,expected) {
  if(!expected) throw new Error('EXPECTED_PARENT_REQUIRED_FOR_REAL_RUN');
  let actual;
  try {actual=cp.execFileSync('git',['-C',root,'rev-parse','HEAD'],{encoding:'utf8',timeout:10000}).trim();}
  catch{throw new Error('PARENT_GIT_VERIFY_FAILED');}
  if(actual!==expected)throw new Error('PARENT_SHA_MISMATCH expected='+expected+' actual='+actual);
  // Parent checkout may have untracked dependency directory only. Reject edits to tracked source and config.
  const changed=cp.execFileSync('git',['-C',root,'status','--porcelain=v1','--untracked-files=all','--','src','packages','tsconfig.json'],{encoding:'utf8',timeout:10000}).trim();
  if(changed)throw new Error('PARENT_SOURCE_OR_CONFIG_DIRTY '+changed.split('\n')[0]);
  return actual;
}
function analyze(root,profile,expected) {
  const rootReal=fs.realpathSync(root);
  const parentSha=verifyParent(rootReal,expected);
  const ts=loadTs(rootReal);
  const opts=readCompilerOptions(ts,rootReal);
  const paths=walk(rootReal,profile);
  if(!paths.length)throw new Error('ZERO_PRODUCTION_FILES');
  const universe=new Set(paths.map(p=>fs.realpathSync(p)));
  const items=[], edges=[];
  for(const p of paths) {
    const source=fs.readFileSync(p,'utf8');
    const kind=p.endsWith('.tsx')?ts.ScriptKind.TSX:ts.ScriptKind.TS;
    const sf=ts.createSourceFile(p,source,ts.ScriptTarget.Latest,true,kind);
    if(sf.parseDiagnostics.length) {
      const err=ts.flattenDiagnosticMessageText(sf.parseDiagnostics[0].messageText,' ');
      throw new Error('SOURCE_PARSE_FAILED '+relNorm(rootReal,p)+' '+err);
    }
    const specs=new Set();collectModuleSpecifiers(ts,sf,specs);
    const imports=[];
    for(const spec of [...specs].sort()) {
      const resolved=ts.resolveModuleName(spec,p,opts,ts.sys).resolvedModule;
      if(!resolved)continue;
      const absolute=path.resolve(resolved.resolvedFileName);
      if(!fs.existsSync(absolute))continue;
      const canon=fs.realpathSync(absolute);
      if(!universe.has(canon))continue;
      const target=relNorm(rootReal,canon),origin=relNorm(rootReal,p);
      imports.push(target);
      edges.push([origin,target]);
    }
    items.push({path:relNorm(rootReal,p),sha256:sha(source),units:collectUnits(ts,sf,source),imports:[...new Set(imports)].sort()});
  }
  edges.sort((a,b)=>a[0].localeCompare(b[0])||a[1].localeCompare(b[1]));
  return {schema:'track04-ts-parent-graph-v2',parent_sha:parentSha,profile,typescript:ts.version,files:items,edges};
}
function main(argv) {
  const args=parseArgs(argv);
  const data=analyze(args.repo,args.profile,args['expected-parent']);
  const output=JSON.stringify(data,null,2)+'\n';
  if(args.out) { fs.mkdirSync(path.dirname(path.resolve(args.out)),{recursive:true});fs.writeFileSync(args.out,output,'utf8'); }
  else process.stdout.write(output);
  return data;
}
if(require.main===module){try{const v=main(process.argv.slice(2)); console.error('T04_TS_G11_PASS files='+v.files.length+' edges='+v.edges.length+' units='+v.files.reduce((x,f)=>x+f.units.length,0));}catch(e){console.error('T04_TS_G1_STOP '+e.message);process.exitCode=1;}}
module.exports={allowedProductionFile,collectModuleSpecifiers,collectUnits,analyze,parseArgs,sha};
