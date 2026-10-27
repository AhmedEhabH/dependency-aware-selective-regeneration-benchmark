#!/usr/bin/env python3
"""Report bounded quality evidence from a qualified D3 E2E, without overclaiming."""
from __future__ import annotations
import argparse
import hashlib
import json
import pathlib

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--results',type=pathlib.Path,required=True)
    ap.add_argument('--out',type=pathlib.Path,required=True)
    a=ap.parse_args()
    if a.out.exists():raise SystemExit('STOP_QUALITY_REPORT_EXISTS')
    root=a.results
    audit=json.loads((root/'D3_JUNIT_AUDIT.json').read_text())
    receipt=json.loads((root/'D3_STAGE/D3_REPAIR_RECEIPT.json').read_text())
    delta=(root/'D3_STAGE/D3_OVER_D2.patch').read_bytes()
    if hashlib.sha256(delta).hexdigest()!=receipt['d3_over_d2_patch_sha256']:
        raise SystemExit('STOP_D3_PATCH_SHA_MISMATCH')
    if audit['junit_integrity_status']!='COMPLETE' or audit['physical_invocations_verified']!=318:
        raise SystemExit('STOP_INCOMPLETE_JUNIT')
    if audit['d3_over_d2_patch_sha256']!=receipt['d3_over_d2_patch_sha256']:
        raise SystemExit('STOP_CANDIDATE_EVIDENCE_SHA_MISMATCH')
    quality={
      'schema':'t11_d3_bounded_code_quality_v1',
      'classification':'TEST_INFORMED_REPAIR_CONTROL_NOT_PROSPECTIVE_MODEL_GENERATION',
      'frozen_original_A5_R1':'STOP',
      'code_identity':{'d3_over_d2_sha256':receipt['d3_over_d2_patch_sha256'],
                       'd3_sources_sha256':receipt['d3_source_sha256']},
      'scope':{'files_modified_from_D2':2,
               'diff_added_lines':sum(x.startswith(b'+') and not x.startswith(b'+++') for x in delta.splitlines()),
               'diff_deleted_lines':sum(x.startswith(b'-') and not x.startswith(b'---') for x in delta.splitlines())},
      'functional':{'stable_F2P':audit['f2p_distinct_stable_pass'],'expected_F2P':3,
                    'stable_P2P':audit['p2p_distinct_stable_pass'],'expected_P2P':103,
                    'verified_physical_invocations':audit['physical_invocations_verified'],
                    'all_stable':audit['f2p_distinct_stable_pass']==3 and audit['p2p_distinct_stable_pass']==103},
      'static':{'ruff_lint':'PASS' if 'All checks passed' in (root/'D3_RUFF_CHECK.log').read_text() else 'CHECK_LOG_REQUIRED',
                'ruff_format':'PASS' if 'already formatted' in (root/'D3_RUFF_FORMAT.log').read_text() else 'NOT_QUALIFIED_CHECK_LOG'},
      'qualifications':{'full_repository_tests':'NOT_RUN','branch_coverage':'NOT_MEASURED',
                        'mutation_score':'NOT_MEASURED','independent_replicates':'NOT_PROVEN_SHARED_DB',
                        'security_review':'NOT_PERFORMED','code_review':'NOT_PERFORMED',
                        'no_model_pass_at_1_claim':True,'no_competitor_comparison':True},
    }
    a.out.write_text(json.dumps(quality,indent=2,sort_keys=True)+'\n')
    print('D3_BOUNDED_QUALITY_REPORT=WRITTEN; FULL_CODE_QUALITY_NOT_PROVEN')
    print('D3_FUNCTIONAL_STABLE='+str(quality['functional']['all_stable']))
if __name__=='__main__':main()
