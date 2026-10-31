import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import cp from 'node:child_process';
const script=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../scripts/evaluate_g2.mjs');
function fixture(mutator=()=>{}) {
 const root=fs.mkdtempSync(path.join(os.tmpdir(),'t04-g2-eval-'));
 for(const arm of ['parent','reference']){
  const dir=path.join(root,arm); fs.mkdirSync(dir);
  for(const name of ['INSTALL','BUILD','TSC','ORACLE','REPEAT','NATIVE']) fs.writeFileSync(path.join(dir,name+'.exit'),'0\n');
  fs.writeFileSync(path.join(dir,'TRACKED_SOURCE_STATUS.txt'),'');
  fs.writeFileSync(path.join(dir,'F2P.json'),JSON.stringify({
   schema:'track04-g2-oracle-v1',
   parent:'a183b02048c5323bcb79f2a03862008466771104',
   reference:'7e1b54d1363ba3f5fe57fe8089babab921a8e9ea',
   classification:arm==='parent'?'RED_DUPLICATED_BASEURL':'GREEN_STABLE_BASEURL',
   observed_requests:[]
  }));
 }
 mutator(root);
 return {root,run:()=>{
  const v=cp.spawnSync(process.execPath,[script,root],{encoding:'utf8'});
  const report=JSON.parse(fs.readFileSync(path.join(root,'G2_EVALUATION.json'),'utf8'));
  return {v,report};
 },cleanup:()=>fs.rmSync(root,{recursive:true,force:true})};
}
test('complete expected RED/GREEN with both original native suites clean gives DIAGNOSTIC PASS',()=>{
 const f=fixture();try{const {v,report}=f.run();assert.equal(v.status,0);assert.equal(report.decision,'DIAGNOSTIC_RED_GREEN_AND_NATIVE_P2P_PASS');}finally{f.cleanup();}
});
test('build or installation error cannot masquerade as parent RED',()=>{
 const f=fixture(root=>fs.writeFileSync(path.join(root,'parent','BUILD.exit'),'1'));
 try{const {v,report}=f.run();assert.equal(v.status,1);assert.equal(report.decision,'STOP');assert.ok(report.reasons.some(s=>s.includes('PARENT_BUILD_NOT_ZERO')));}finally{f.cleanup();}
});
test('regression in original native suite fails even with successful F2P',()=>{
 const f=fixture(root=>fs.writeFileSync(path.join(root,'reference','NATIVE.exit'),'1'));
 try{const {v,report}=f.run();assert.equal(v.status,1);assert.equal(report.decision,'STOP');assert.ok(report.reasons.some(s=>s.includes('REFERENCE_NATIVE_NOT_ZERO')));}finally{f.cleanup();}
});
test('dirty historical source checkout fails closed',()=>{
 const f=fixture(root=>fs.writeFileSync(path.join(root,'parent','TRACKED_SOURCE_STATUS.txt'),' M src/fetch.ts\n'));
 try{const {v,report}=f.run();assert.equal(v.status,1);assert.ok(report.reasons.includes('PARENT_TRACKED_SOURCE_DIRTY'));}finally{f.cleanup();}
});
