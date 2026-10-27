#!/usr/bin/env python3
"""Offline post-hoc D2 replay; NEVER modifies original A5-R1 result or calls an API."""
import argparse, hashlib, importlib.util, json, pathlib, tempfile, zipfile

EXPECTED_KIT_SHA = 'cb55efa0abe06cbef5592ae21427c824d8ca64f844a1d3ad8e70543b7af8fbf9'
EXPECTED_EVIDENCE_SHA = '1ecf859670c7946ed47083422e627febf7cf182d8af61430cec919e38c4a1d2b'
EXPECTED_PATCH_SHA = 'de027cdf63d9badf221fd6ec0807a0425aa54a4e8c5da005629f1c69f396277f'
ENGINE_PATH = 'GENERATOR_ONLY/T11_A5_ENGINE.py'
PARENT_PATH = 'GENERATOR_ONLY/PARENT_ONLY_A4_REQUEST.json'

def sha(b): return hashlib.sha256(b).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--kit',required=True,type=pathlib.Path)
    ap.add_argument('--evidence',required=True,type=pathlib.Path)
    ap.add_argument('--out',required=True,type=pathlib.Path)
    a=ap.parse_args()
    if sha(a.kit.read_bytes()) != EXPECTED_KIT_SHA: raise SystemExit('STOP_KIT_SHA_MISMATCH')
    if sha(a.evidence.read_bytes()) != EXPECTED_EVIDENCE_SHA: raise SystemExit('STOP_EVIDENCE_SHA_MISMATCH')
    if a.out.exists():raise SystemExit('STOP_OUTPUT_EXISTS')
    with zipfile.ZipFile(a.evidence) as evidence, zipfile.ZipFile(a.kit) as kit, tempfile.TemporaryDirectory() as td:
        base=pathlib.Path(td)/'GENERATOR_ONLY';base.mkdir()
        for fp in (ENGINE_PATH,PARENT_PATH):
            (base/pathlib.Path(fp).name).write_bytes(kit.read(fp))
        spec=importlib.util.spec_from_file_location('t11_a5_original_engine',base/'T11_A5_ENGINE.py')
        eng=importlib.util.module_from_spec(spec); spec.loader.exec_module(eng)
        receipt=json.loads(evidence.read('A5_R1_RESULT_RECEIPT.json'))
        original=evidence.read('MODEL_COMPLETION_EXACT_UTF8.txt')
        if sha(original)!=receipt['model_content_sha256']:raise SystemExit('STOP_MODEL_COMPLETION_SHA')
        edits=json.loads(original)['edits']
        if len(edits)!=4 or edits[2]['old_lines']!=edits[2]['new_lines']:raise SystemExit('STOP_DIAGNOSTIC_PRECONDITION')
        try: eng.parse_edits(original.decode('utf-8'))
        except ValueError as exc:
            if 'EDIT_2_NOOP_STOP' not in str(exc):raise
        else:raise SystemExit('STOP_ORIGINAL_DID_NOT_FAIL')
        _,parents=eng.request()
        diff,lf,crlf=eng.render(eng.parse_edits(json.dumps({'edits':edits[:2]+edits[3:]})),parents)
        if sha(diff)!=EXPECTED_PATCH_SHA:raise SystemExit('STOP_D2_PATCH_SHA_DRIFT')
        a.out.mkdir(parents=True)
        (a.out/'D2_DIAGNOSTIC_PATCH_LF.diff').write_bytes(diff)
        (a.out/'D2_GENERATED_SOURCE_SHA256_LF.json').write_text(json.dumps(lf,indent=2,sort_keys=True)+'\n')
        (a.out/'D2_GENERATED_SOURCE_SHA256_CRLF.json').write_text(json.dumps(crlf,indent=2,sort_keys=True)+'\n')
        print('D2_POST_HOC_REPLAY=PASS; GIT_APPLY_AND_AST=PASS')
        print('ORIGINAL_A5_R1=PATCH_QUALIFICATION_FAIL_NO_RETRY')
        print('DIAGNOSTIC_PATCH_SHA256='+sha(diff))
        print('GENERATED_CODE_BEHAVIORAL_TESTS=NOT_RUN')

if __name__=='__main__':main()
