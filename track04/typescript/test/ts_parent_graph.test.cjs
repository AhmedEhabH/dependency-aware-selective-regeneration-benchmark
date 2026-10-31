'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),cp=require('node:child_process');
const {analyze,allowedProductionFile}=require('../src/ts_parent_graph.cjs');
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
