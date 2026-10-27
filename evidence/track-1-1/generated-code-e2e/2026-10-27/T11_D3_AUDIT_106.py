#!/usr/bin/env python3
"""Independent D3 test-informed repair-control auditor, read-only. Never grants official A5 success."""
from __future__ import annotations
import argparse, collections, datetime, hashlib, json, pathlib, sys, xml.etree.ElementTree as ET

HERE=pathlib.Path(__file__).resolve().parent
PATCH=None  # supplied from exact D3 repair receipt, not a frozen model candidate
FIXED={'F2P':('R7_FROZEN_NODES.json','f547b88af226ba8ed0c1745c77bf6b90b1f12f5d2e715013c47234e4fcd98cf9',3),
       'P2P':('R8_FROZEN_NODES.json','d3392709e5b6a62dd885fc9a29845888259285542a622bb78687f9ff4bfea9a0',103)}
def sha(f):return hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest()
def load_nodes():
 out={}
 for stage,(name,expected,n) in FIXED.items():
  f=HERE/name
  if sha(f)!=expected:raise ValueError('NODE_LIST_BYTES_DRIFT_'+stage)
  data=json.loads(f.read_text('utf8'))
  if not isinstance(data,list) or len(data)!=n or len(set(data))!=n or any(type(x)!=str for x in data):raise ValueError('NODE_COUNT_OR_FORMAT_'+stage)
  out[stage]=data
 if set(out['F2P'])&set(out['P2P']):raise ValueError('F2P_P2P_OVERLAP')
 return out

def junit_status(f,node):
 try:
  tree=ET.parse(f); cases=tree.findall('.//testcase')
  if len(cases)!=1:return 'INVALID_JUNIT','JUNIT_CASE_COUNT_'+str(len(cases))
  case=cases[0]; name=case.get('name',''); classname=case.get('classname','')
  expected_name=node.rsplit('::',1)[-1]
  # pytest may remove parameter bracket from classname, but test name must be exact.
  if name!=expected_name:return 'INVALID_JUNIT','JUNIT_NAME_MISMATCH'
  if not classname:return 'INVALID_JUNIT','JUNIT_CLASSNAME_EMPTY'
  if case.find('error') is not None:return 'ERROR','pytest_error'
  if case.find('failure') is not None:return 'FAIL','pytest_failure'
  if case.find('skipped') is not None:return 'SKIP','pytest_skipped'
  return 'PASS',''
 except (ET.ParseError, OSError) as ex:return 'INVALID_JUNIT',str(ex)[:120]

def audit(root, patch_sha):
 expected=load_nodes()
 report={'schema':'t11_d3_test_informed_repair_106_junit_audit_v1','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'classification':'TEST_INFORMED_REPAIR_CONTROL_NOT_MODEL_PASS_AT_1','original_a5_r1':'PATCH_QUALIFICATION_FAIL_NO_RETRY',
         'task':'saleor-rc-7e42fc67ce72','frozen_neg_tree_oid':'65cd0b6e07e73c102ae600fea0fabea827b7fe29',
         'd3_over_d2_patch_sha256':patch_sha,'distinct_expected':106,'physical_invocations_expected':318,
         'stages':{},'scientific_independent_repetitions':False,'model_api_calls_during_evaluator':0,
         'limits':'This only audits outputs, not OCI/DB isolation or original generated pass@1'}
 for stage,nodes in expected.items():
  d=root/stage; ledger=d/'COMMAND_LEDGER.jsonl'
  records=[]; errors=[]; statuses=collections.Counter(); per_node={node:[] for node in nodes}; wall=0.0
  if ledger.is_file():
   try:records=[json.loads(x) for x in ledger.read_text('utf8').splitlines() if x.strip()]
   except (ValueError,OSError) as exc:errors.append('LEDGER_PARSE_ERROR:'+str(exc)[:100])
  seen=set()
  for row in records:
   try:
    rep=row['repetition'];idx=row['index'];node=row['node'];key=(rep,idx)
    if type(rep)!=int or type(idx)!=int or rep not in range(3) or idx not in range(len(nodes)) or node!=nodes[idx] or row['stage']!=stage or key in seen:raise ValueError('LEDGER_IDENTITY_OR_DUPLICATE')
    seen.add(key)
    if not isinstance(row['return_code'],int):raise ValueError('RC_MISSING')
    wall+=float(row['wall_seconds'])
    xml=d/f'r{rep}_f{idx}.xml'; log=d/f'r{rep}_f{idx}.stdout_stderr.log'
    if not xml.is_file(): raise ValueError('XML_MISSING')
    if row['xml_sha256']!=sha(xml):raise ValueError('XML_SHA_CHANGED')
    if not log.is_file() or row['log_sha256']!=sha(log):raise ValueError('LOG_SHA_CHANGED')
    outcome,reason=junit_status(xml,node)
    statuses[outcome]+=1
    per_node[node].append({'repeat':rep,'rc':row['return_code'],'outcome':outcome,'xml_sha256':sha(xml),'log_sha256':sha(log),'reason':reason})
    if row['return_code'] not in (0,1) or row.get('timeout') or outcome=='INVALID_JUNIT':errors.append(f'{rep}:{idx}:INFRA_OR_JUNIT')
    if (outcome=='PASS' and row['return_code']!=0) or (outcome in ('FAIL','ERROR') and row['return_code']!=1):
     errors.append(f'{rep}:{idx}:RETURN_CODE_JUNIT_DISAGREEMENT')
   except (KeyError,ValueError,TypeError,OSError) as exc:errors.append(str(exc)[:130])
  # Detect if orphan files exist, which might indicate test splicing.
  if d.exists():
   observed={x.name for x in d.glob('*.xml')}
   expected_names={f'r{rep}_f{idx}.xml' for rep in range(3) for idx in range(len(nodes))}
   if observed-expected_names:errors.append('EXTRA_JUNIT_FILES:'+str(len(observed-expected_names)))
  full= len(records)==len(nodes)*3 and len(seen)==len(nodes)*3 and not errors
  stable_success=sum(len(v)==3 and all(x['outcome']=='PASS' for x in v) for v in per_node.values())
  stable_fail=sum(len(v)==3 and any(x['outcome']=='FAIL' for x in v) for v in per_node.values())
  flaky=sum(len(v)==3 and len(set(x['outcome'] for x in v))>1 for v in per_node.values())
  report['stages'][stage]={'expected_nodes':len(nodes),'expected_invocations':len(nodes)*3,'ledger_invocations':len(records),
                           'verified_invocations':len(seen),'outcome_count':dict(statuses),'stable_pass_nodes':stable_success,
                           'nodes_with_failures':stable_fail,'mixed_repeat_nodes':flaky,'wall_seconds_sum':round(wall,2),
                           'ledger_sha256':sha(ledger) if ledger.is_file() else None,
                           'errors':errors,'complete_and_integrity_checked':full,'by_node':per_node}
 report['physical_invocations_verified']=sum(s['verified_invocations'] for s in report['stages'].values())
 report['f2p_distinct_stable_pass']=report['stages']['F2P']['stable_pass_nodes']
 report['p2p_distinct_stable_pass']=report['stages']['P2P']['stable_pass_nodes']
 report['junit_integrity_status']='COMPLETE' if all(s['complete_and_integrity_checked'] for s in report['stages'].values()) else 'INCOMPLETE_OR_INTEGRITY_STOP'
 report['full_behavioral_provenance']='NOT_ESTABLISHED_BY_JUNIT_AUDIT_ALONE'
 return report

def main():
 p=argparse.ArgumentParser();p.add_argument('--results',required=True,type=pathlib.Path);p.add_argument('--out',required=True,type=pathlib.Path);p.add_argument('--repair-receipt',required=True,type=pathlib.Path);a=p.parse_args()
 if a.out.exists():raise SystemExit('STOP_REPORT_ALREADY_EXISTS')
 receipt=json.loads(a.repair_receipt.read_text());assert receipt['candidate']=='D3_TEST_INFORMED_REPAIR_CONTROL';assert len(receipt['d3_over_d2_patch_sha256'])==64;report=audit(a.results, receipt['d3_over_d2_patch_sha256']);a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
 print('D3_JUNIT_LEDGER='+report['junit_integrity_status'])
 print('F2P_STABLE_PASS='+str(report['f2p_distinct_stable_pass'])+'/3; P2P_STABLE_PASS='+str(report['p2p_distinct_stable_pass'])+'/103')
 print('PHYSICAL_VERIFIED='+str(report['physical_invocations_verified'])+'/318')
 print('REPORT='+str(a.out))
 return 0 if report['junit_integrity_status']=='COMPLETE' else 3
if __name__=='__main__':sys.exit(main())
