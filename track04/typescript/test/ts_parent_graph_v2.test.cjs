'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),cp=require('node:child_process');
const {analyze,allowedProductionFile}=require('../src/ts_parent_graph_v2.cjs');
const emit=(r,p,s)=>{const f=path.join(r,p);fs.mkdirSync(path.dirname(f),{recursive:true});fs.writeFileSync(f,s);};
const sh=(r,...cmd)=>cp.execFileSync('git',['-C',r,...cmd],{stdio:'pipe',encoding:'utf8'}).trim();
const withRepo=(callback)=>{
 const root=fs.mkdtempSync(path.join(os.tmpdir(),'t04-ts-g1-'));
 try{
  emit(root,'package.json','{"name":"test","private":true}');
  emit(root,'tsconfig.json',JSON.stringify({compilerOptions:{target:'ES2022',module:'NodeNext',moduleResolution:'NodeNext',strict:true}},null,2));
  fs.mkdirSync(path.join(root,'node_modules'),{recursive:true});
  // The selftest only uses the locally preinstalled TS version by this explicit test-only shim.
  const tsPath=require.resolve('typescript');
  emit(root,'node_modules/typescript/package.json',JSON.stringify({name:'typescript',main:tsPath}));
  sh(root,'init','-q');sh(root,'-c','user.name=T04','-c','user.email=track04@example.invalid','add','.');
  callback(root,{emit:(p,s)=>emit(root,p,s),commit:()=>{sh(root,'add','.');sh(root,'-c','user.name=T04','-c','user.email=track04@example.invalid','commit','-qm','fixture');return sh(root,'rev-parse','HEAD');}});
 } finally {fs.rmSync(root,{recursive:true,force:true});}
};
test('production-only file selection and exclusions',()=>{
 assert.equal(allowedProductionFile('src/index.ts','tinybench'),true);
 assert.equal(allowedProductionFile('src/deep/x.tsx','tinybench'),true);
 assert.equal(allowedProductionFile('src/x.spec.ts','tinybench'),false);
 assert.equal(allowedProductionFile('src/x.d.ts','tinybench'),false);
 assert.equal(allowedProductionFile('test/index.ts','tinybench'),false);
 assert.equal(allowedProductionFile('src/generated/x.ts','tinybench'),false);
 assert.equal(allowedProductionFile('packages/core/src/nested/x.ts','nestjs'),true);
 assert.equal(allowedProductionFile('packages/core/test/x.ts','nestjs'),false);
});
test('parent-only graph: imports and exported units deterministic',()=>withRepo((root,h)=>{
 h.emit('src/b.ts',`export const b = 5; export class Bee { work(): number {return b;} }\n`);
 h.emit('src/a.ts',`import { b } from './b';\nexport function sum(x: number): number { return x+b; }\nexport const fn = (x: number): number => x+b;\nexport class A { async work(): Promise<number> { return b; } }\n`);
 h.emit('src/reexport.ts',`export { b } from './b';\n`);
 h.emit('src/external.ts',`import { a } from 'not-local-dependency';\n`);
 h.emit('src/should.spec.ts','throw new Error("NEVER_READ");');
 h.emit('test/wrong.ts','throw new Error("NEVER_READ");');
 const sha=h.commit(), r=analyze(root,'tinybench',sha);
 assert.deepEqual(r.files.map(f=>f.path),['src/a.ts','src/b.ts','src/external.ts','src/reexport.ts']);
 assert.deepEqual(r.edges,[['src/a.ts','src/b.ts'],['src/reexport.ts','src/b.ts']]);
 const a=r.files[0];assert.ok(a.units.some(u=>u.kind==='function'&&u.name==='sum'));
 assert.ok(a.units.some(u=>u.kind==='function_expression'&&u.name==='fn'));
 assert.ok(a.units.some(u=>u.kind==='method'&&u.name==='work'));
 assert.equal(JSON.stringify(analyze(root,'tinybench',sha)),JSON.stringify(r));
 assert.throws(()=>analyze(root,'tinybench','0'.repeat(40)),/PARENT_SHA_MISMATCH/);
}));
test('fail-closed when a tracked source file changed',()=>withRepo((root,h)=>{
 h.emit('src/a.ts','export function f(): number { return 1; }');
 const sha=h.commit();h.emit('src/a.ts','export function f(): number { return 2; }');
 assert.throws(()=>analyze(root,'tinybench',sha),/PARENT_SOURCE_OR_CONFIG_DIRTY/);
}));
test('parse errors must STOP instead of silently making false graphs',()=>withRepo((root,h)=>{
 h.emit('src/bad.ts','export function x( {');const sha=h.commit();
 assert.throws(()=>analyze(root,'tinybench',sha),/SOURCE_PARSE_FAILED/);
}));
test('nested NestJS-style package universe',()=>withRepo((root,h)=>{
 h.emit('packages/core/src/a.ts',`import { b } from './b';export const foo = ()=>b`);
 h.emit('packages/core/src/b.ts',`export const b=42`);
 h.emit('packages/core/test/o.ts',`bad bad bad`);
 const sha=h.commit(),r=analyze(root,'nestjs',sha);
 assert.equal(r.files.length,2);assert.deepEqual(r.edges,[['packages/core/src/a.ts','packages/core/src/b.ts']]);
}));

test('fail-closed when an untracked production source is present',()=>withRepo((root,h)=>{
 h.emit('src/a.ts','export const a=1;'); const sha=h.commit();
 h.emit('src/injected.ts','export const injected=999;');
 assert.throws(()=>analyze(root,'tinybench',sha),/PARENT_SOURCE_OR_CONFIG_DIRTY/);
}));
test('fail-closed when tsconfig is modified after freeze',()=>withRepo((root,h)=>{
 h.emit('src/a.ts','export const a=1;'); const sha=h.commit();
 h.emit('tsconfig.json','{"compilerOptions":{"strict":false}}');
 assert.throws(()=>analyze(root,'tinybench',sha),/PARENT_SOURCE_OR_CONFIG_DIRTY/);
}));
test('static graph includes literal dynamic imports and type-only imports',()=>withRepo((root,h)=>{
 h.emit('src/a.ts',`import type {B} from './b';
export const load = async()=>import('./b');
`);
 h.emit('src/b.ts',`export type B = number;`);
 const sha=h.commit(),r=analyze(root,'tinybench',sha);
 assert.deepEqual(r.files.find(f=>f.path==='src/a.ts').imports,['src/b.ts']);
 assert.deepEqual(r.edges,[['src/a.ts','src/b.ts']]);
}));


test('TypeScript public declarations and re-exports remain indexed',()=>withRepo((root,h)=>{
 h.emit('src/types.ts',`export interface User { id: string }\nexport type Id = string;\nexport enum Status { Good = 1 }\n`);
 h.emit('src/index.ts',`export type { User, Id } from './types';\nexport * from './types';\n`);
 h.emit('src/constants.ts',`export const values = {a: 1,b: 2} as const;\n`);
 const sha=h.commit(),r=analyze(root,'tinybench',sha);
 assert.equal(r.schema,'track04-ts-parent-graph-v2');
 const types=r.files.find(f=>f.path==='src/types.ts');
 assert.deepEqual(types.units.map(u=>u.kind),['interface','type_alias','enum']);
 assert.deepEqual(r.files.find(f=>f.path==='src/index.ts').units.map(u=>u.kind),
   ['export_declaration','export_declaration']);
 assert.deepEqual(r.files.find(f=>f.path==='src/constants.ts').units.map(u=>u.kind),
   ['variable_declaration']);
 assert.deepEqual(r.files.find(f=>f.path==='src/index.ts').imports,['src/types.ts']);
 assert.ok(r.files.every(f=>f.units.length>0));
 assert.equal(JSON.stringify(r),JSON.stringify(analyze(root,'tinybench',sha)));
}));

test('empty or imports-only module is never silently zero-indexed',()=>withRepo((root,h)=>{
 h.emit('src/a.ts',`import 'not-present';\n`);
 h.emit('src/b.ts',`// legitimate side-effect-only or empty file\n`);
 const sha=h.commit(),r=analyze(root,'tinybench',sha);
 assert.deepEqual(r.files.map(f=>f.units.map(u=>u.kind)),
   [['module_fallback'],['module_fallback']]);
}));

test('every declaration unit SHA matches exact parent text slice',()=>withRepo((root,h)=>{
 const s=`/** JSDoc */\nexport interface X { foo: string }\nexport const x = 42;\nexport function y(): number { return x }\n`;
 h.emit('src/a.ts',s);
 const sha=h.commit(),r=analyze(root,'tinybench',sha);
 const content=fs.readFileSync(path.join(root,'src/a.ts'),'utf8');
 const ts=require('typescript');const sf=ts.createSourceFile('a.ts',content,ts.ScriptTarget.Latest,true);
 const units=r.files[0].units;
 assert.ok(units.length>=3);
 const all=[];
 const visit=n=>{all.push(n);ts.forEachChild(n,visit)};visit(sf);
 for(const u of units){
  const matches=all.filter(n=>{
   const start=n.getStart(sf,false),end=n.end;
   const h=require('node:crypto').createHash('sha256').update(content.slice(start,end)).digest('hex');
   return h===u.sha256;
  });
  assert.ok(matches.length>=1,`unit without exact AST-source match: ${u.kind}`);
  const m=matches[0];
  assert.equal(u.start_line,sf.getLineAndCharacterOfPosition(m.getStart(sf,false)).line+1);
  assert.equal(u.end_line,sf.getLineAndCharacterOfPosition(m.end).line+1);
 }
}));


test('UTF-16 offsets reconstruct every indexed unit including astral unicode',()=>withRepo((root,h)=>{
 const value='// 🧪 comment\nexport interface Book { title: string }\nexport const count = 5;\n';
 h.emit('src/a.ts',value);
 h.emit('src/onlyImports.ts',"import 'optional-nonexistent';\n");
 const sha=h.commit(),r=analyze(root,'tinybench',sha);
 for(const f of r.files){
  const content=fs.readFileSync(path.join(root,f.path),'utf8');
  for(const u of f.units){
   assert.equal(Number.isInteger(u.start_offset_utf16),true);
   assert.equal(Number.isInteger(u.end_offset_utf16),true);
   assert.ok(u.start_offset_utf16>=0 && (u.start_offset_utf16<u.end_offset_utf16 || (u.kind==='module_fallback' && content.length===0 && u.start_offset_utf16===0 && u.end_offset_utf16===0)));
   assert.ok(u.end_offset_utf16<=content.length);
   const excerpt=content.slice(u.start_offset_utf16,u.end_offset_utf16);
   const digest=require('node:crypto').createHash('sha256').update(excerpt,'utf8').digest('hex');
   assert.equal(digest,u.sha256,`${f.path}:${u.kind}`);
   const first=content.slice(0,u.start_offset_utf16).split('\n').length;
   const last=content.slice(0,u.end_offset_utf16).split('\n').length;
   assert.equal(u.start_line,first); assert.equal(u.end_line,last);
  }
 }
}));


test('empty production module keeps verifiable zero-length fallback',()=>withRepo((root,h)=>{
 h.emit('src/empty.ts','');
 const sha=h.commit(),r=analyze(root,'tinybench',sha);
 assert.equal(r.files.length,1);
 const u=r.files[0].units[0];
 assert.equal(u.kind,'module_fallback');
 assert.equal(u.start_offset_utf16,0); assert.equal(u.end_offset_utf16,0);
 assert.equal(u.sha256,require('node:crypto').createHash('sha256').update('').digest('hex'));
}));
