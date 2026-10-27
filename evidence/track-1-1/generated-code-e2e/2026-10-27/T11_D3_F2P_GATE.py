#!/usr/bin/env python3
"""Independent fail-closed F2P gate. All 9 runs must pass before P2P is attempted."""
from __future__ import annotations
import argparse
import hashlib
import json
import pathlib
import xml.etree.ElementTree as ET

FROZEN_R7_SHA = 'f547b88af226ba8ed0c1745c77bf6b90b1f12f5d2e715013c47234e4fcd98cf9'
HERE=pathlib.Path(__file__).resolve().parent

def sha(b):return hashlib.sha256(b).hexdigest()

def audit(folder:pathlib.Path)->dict:
    nodes_path=HERE/'R7_FROZEN_NODES.json'
    if sha(nodes_path.read_bytes())!=FROZEN_R7_SHA:raise ValueError('STOP_FROZEN_R7_SHA')
    nodes=json.loads(nodes_path.read_text())
    if len(nodes)!=3 or len(set(nodes))!=3:raise ValueError('STOP_NODES_NOT_3')
    ledger=folder/'COMMAND_LEDGER.jsonl'
    recs=[json.loads(l) for l in ledger.read_text().splitlines() if l.strip()]
    if len(recs)!=9:raise ValueError('STOP_LEDGER_NOT_9')
    seen=set(); failed=[];all_pass=True
    for rec in recs:
        rep,idx=rec['repetition'],rec['index']
        if type(rep)!=int or type(idx)!=int or rep not in range(3) or idx not in range(3):raise ValueError('STOP_INVALID_INDEX')
        if (rep,idx) in seen or rec['node']!=nodes[idx] or rec['stage']!='F2P':raise ValueError('STOP_LEDGER_IDENTITY')
        seen.add((rep,idx))
        xml=folder/f'r{rep}_f{idx}.xml'; log=folder/f'r{rep}_f{idx}.stdout_stderr.log'
        if not xml.is_file() or not log.is_file():raise ValueError('STOP_MISSING_RAW')
        if sha(xml.read_bytes())!=rec['xml_sha256'] or sha(log.read_bytes())!=rec['log_sha256']:raise ValueError('STOP_JUNIT_OR_LOG_SHA')
        case=ET.parse(xml).findall('.//testcase')
        if len(case)!=1 or case[0].get('name')!=nodes[idx].split('::')[-1]:raise ValueError('STOP_JUNIT_CASE_IDENTITY')
        passit=rec['return_code']==0 and not rec['timeout'] and all(case[0].find(t) is None for t in ('failure','error','skipped'))
        if not passit:all_pass=False;failed.append({'node':nodes[idx],'repeat':rep,'return_code':rec['return_code']})
    if len(seen)!=9:raise ValueError('STOP_MISSING_INVOCATION')
    if {f.name for f in folder.glob('*.xml')}!={f'r{rep}_f{idx}.xml' for rep in range(3) for idx in range(3)}:raise ValueError('STOP_EXTRA_XML')
    return {'schema':'t11_d3_f2p_gate_v1','frozen_nodes':3,'verified_invocations':9,'all_f2p_stable_pass':all_pass,
            'failed_invocations':failed,'verdict':'PASS' if all_pass else 'FUNCTIONAL_FAIL_STOP_P2P',
            'original_model_a5_r1':'STOP','candidate':'D3_TEST_INFORMED_REPAIR_CONTROL'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--results',required=True,type=pathlib.Path);p.add_argument('--out',required=True,type=pathlib.Path); a=p.parse_args()
    if a.out.exists():raise SystemExit('STOP_GATE_REPORT_EXISTS')
    try: report=audit(a.results)
    except Exception as exc:
        report={'verdict':'INFRA_OR_EVIDENCE_STOP','error':str(exc),'candidate':'D3_TEST_INFORMED_REPAIR_CONTROL'}
    a.out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('D3_F2P_GATE='+report['verdict'])
    print('F2P_GATE_REPORT='+str(a.out))
    return 0 if report['verdict']=='PASS' else 2
if __name__=='__main__':raise SystemExit(main())
