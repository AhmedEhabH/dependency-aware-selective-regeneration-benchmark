#!/usr/bin/env node
// Fail closed, distinguish expected RED from missing/broken harness.
import fs from 'node:fs';
import path from 'node:path';
const root=path.resolve(process.argv[2]||'evidence');
const slurp=(p)=>fs.existsSync(p)?fs.readFileSync(p,'utf8').trim():null;
const status={schema:'track04-g2-eval-v1',interpretation:'DIAGNOSTIC_ONLY_NOT_BLINDED',arms:{},decision:'STOP',reasons:[]};
for(const arm of ['parent','reference']) {
 const dir=path.join(root,arm), exit={};
 for(const name of ['INSTALL','BUILD','TSC','ORACLE','REPEAT','NATIVE']) {
   const raw=slurp(path.join(dir,name+'.exit'));
   exit[name]=raw!==null && /^\d+$/.test(raw)?Number(raw):null;
 }
 let oracle=null;
 try{oracle=JSON.parse(fs.readFileSync(path.join(dir,'F2P.json'),'utf8'));}
 catch(e){status.reasons.push(arm.toUpperCase()+'_ORACLE_JSON_MISSING_OR_INVALID');}
 status.arms[arm]={exit,classification:oracle?.classification??null,requests:oracle?.observed_requests??null};
 if(oracle && (oracle.parent!=='a183b02048c5323bcb79f2a03862008466771104' || oracle.reference!=='7e1b54d1363ba3f5fe57fe8089babab921a8e9ea')) status.reasons.push(arm.toUpperCase()+'_ORACLE_IDENTITY_MISMATCH');
 if(slurp(path.join(dir,'TRACKED_SOURCE_STATUS.txt')) !== '') status.reasons.push(arm.toUpperCase()+'_TRACKED_SOURCE_DIRTY');
 for(const name of ['INSTALL','BUILD','TSC','ORACLE','REPEAT','NATIVE']) if(exit[name]!==0) status.reasons.push(arm.toUpperCase()+'_'+name+'_NOT_ZERO_'+String(exit[name]));
}
if(status.arms.parent.classification!=='RED_DUPLICATED_BASEURL')status.reasons.push('PARENT_NOT_RED_FOR_SPECIFIED_BUG');
if(status.arms.reference.classification!=='GREEN_STABLE_BASEURL')status.reasons.push('REFERENCE_NOT_GREEN_FOR_SPECIFIED_BUG');
if(status.reasons.length===0)status.decision='DIAGNOSTIC_RED_GREEN_AND_NATIVE_P2P_PASS';
fs.mkdirSync(root,{recursive:true});fs.writeFileSync(path.join(root,'G2_EVALUATION.json'),JSON.stringify(status,null,2)+'\n');
console.log('TRACK04_G2_DECISION='+status.decision);
console.log('TRACK04_G2_REASONS='+JSON.stringify(status.reasons));
// An eligible scientific/hidden benchmark still requires evaluator custody and issue-body as-of.
if(status.reasons.length)process.exitCode=1;
