#!/usr/bin/env python3
"""Export bounded public conclusions ONLY; never copies test logs or DB secrets."""
from __future__ import annotations
import argparse,hashlib,json,pathlib

def sha(p:pathlib.Path):return hashlib.sha256(p.read_bytes()).hexdigest()

def produce(root:pathlib.Path,dest:pathlib.Path)->dict:
    if dest.exists():raise ValueError('STOP_PUBLIC_SUMMARY_ALREADY_EXISTS')
    # The source is local raw results. Read a strict allowlist; do not include untrusted log strings.
    repair=root/'D3_STAGE/D3_REPAIR_RECEIPT.json'
    status='INFRASTRUCTURE_STOP_BEFORE_REPAIR' if not repair.is_file() else 'EVALUATION_INCOMPLETE'
    j={'schema':'t11_d3_public_safe_summary_v1','classification':'TEST_INFORMED_REPAIR_CONTROL_NOT_MODEL_PASS_AT_1',
       'official_A5_R1':'STOP','previous_D2_F2P_stable_pass':1,'previous_D2_P2P_stable_pass':103,
       'd3_repair_patch_sha256':None,'d3_source_sha256':None,
       'f2p_stable_pass':None,'p2p_stable_pass':None,'verified_invocations':None,'status':status,
       'disclosures':['The repair used previously observed frozen F2P failures','Shared DB means physical repeats are not independent statistical replicates',
                      'Chosen P2P subset is not the full repository test suite',
                      'Security audit, mutation score and coverage remain unqualified']}
    if repair.is_file():
       rec=json.loads(repair.read_text()); assert rec['candidate']=='D3_TEST_INFORMED_REPAIR_CONTROL'
       patch=root/'D3_STAGE/D3_OVER_D2.patch'
       assert patch.is_file() and sha(patch)==rec['d3_over_d2_patch_sha256']
       j['d3_repair_patch_sha256']=rec['d3_over_d2_patch_sha256'];j['d3_source_sha256']=rec['d3_source_sha256']
    f2p=root/'D3_F2P_GATE.json'
    if f2p.is_file():
       f=json.loads(f2p.read_text());assert f['candidate']=='D3_TEST_INFORMED_REPAIR_CONTROL'
       if f['verdict']=='PASS':j['f2p_stable_pass']=3
       elif f['verdict']=='FUNCTIONAL_FAIL_STOP_P2P':
          j['f2p_stable_pass']=3-len(set(x['node'] for x in f['failed_invocations']))
          j['status']='D3_F2P_FUNCTIONAL_FAIL_P2P_NOT_RUN'
       else:j['status']='D3_F2P_EVIDENCE_STOP'
    audit=root/'D3_JUNIT_AUDIT.json'
    if audit.is_file():
       a=json.loads(audit.read_text())
       if a['junit_integrity_status']=='COMPLETE' and a['physical_invocations_verified']==318:
          j['f2p_stable_pass']=a['f2p_distinct_stable_pass']
          j['p2p_stable_pass']=a['p2p_distinct_stable_pass']
          j['verified_invocations']=318
          j['status']='D3_COMPLETE_CONTROL_PASS' if j['f2p_stable_pass']==3 and j['p2p_stable_pass']==103 else 'D3_COMPLETE_CONTROL_FUNCTIONAL_FAIL'
       else:j['status']='D3_AUDIT_INTEGRITY_STOP'
    if j['status']=='EVALUATION_INCOMPLETE':j['status']='D3_EXECUTION_STOP_BEFORE_FINAL_AUDIT'
    dest.mkdir(parents=True)
    (dest/'D3_PUBLIC_SUMMARY.json').write_text(json.dumps(j,sort_keys=True,indent=2)+'\n')
    lines=['# D3 test-informed repair control — research milestone','',
           f"- **State:** `{j['status']}`",f"- **Official A5-R1:** `STOP` (unchanged)",
           '- **D2 baseline:** 1/3 F2P, 103/103 selected P2P, 318 JUnit invocations',
           '- **D3 intervention:** move default token creation inside tokenTargetUrl guard; reject non-APP_PAGE relative extension without appUrl',
           f"- **D3 F2P stable:** `{j['f2p_stable_pass']}/3`" if j['f2p_stable_pass'] is not None else '- **D3 F2P:** not qualified',
           f"- **D3 P2P stable:** `{j['p2p_stable_pass']}/103`" if j['p2p_stable_pass'] is not None else '- **D3 P2P:** not run or not qualified',
           f"- **Verified physical invocations:** `{j['verified_invocations']}`" if j['verified_invocations'] is not None else '- **Complete JUnit audit:** not qualified',
           f"- **D3 over D2 SHA-256:** `{j['d3_repair_patch_sha256']}`" if j['d3_repair_patch_sha256'] else '- **D3 patch SHA:** no qualified repair receipt',
           '', '## Scientific limits', '- This was engineered *after inspecting frozen F2P failures*; it is not blind model pass@1, independent regeneration evidence, or a competitor comparison.',
           '- The 3 repeated pytest invocations per node shared DB/runtime. Results do not prove independent replicates, complete code quality, mutation score, or security.',
           '- Raw execution logs and test XML remain local; no logs, tokens, environment variables or DB identifiers are embedded in this public report.',
           '']
    (dest/'D3_PUBLIC_SUMMARY.md').write_text('\n'.join(lines))
    print('D3_PUBLIC_RESULT='+j['status'])
    return j

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--results',type=pathlib.Path,required=True);ap.add_argument('--out',type=pathlib.Path,required=True);args=ap.parse_args()
 produce(args.results,args.out)
if __name__=='__main__':main()
