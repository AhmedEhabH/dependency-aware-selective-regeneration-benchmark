#!/usr/bin/env python3
"""Read-only audit of T11 D2 original evidence ZIP. Never modifies the ZIP or code."""
import argparse
import collections
import hashlib
import json
import re
import sys
import zipfile
from xml.etree import ElementTree

EXPECTED_ZIP_SHA = 'b3327793e5c926d6621bbb694fa231fb5a35f535e62d89112b5bf832f472463a'
EXPECTED_AUDIT_SHA = '02b1779cb21bc10d659d77fc06a82b1e03ad7a5ec6b1ac9e08aea34175ba02c7'
EXPECTED_PATCH_SHA = 'de027cdf63d9badf221fd6ec0807a0425aa54a4e8c5da005629f1c69f396277f'

def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()

def verify(path):
    with open(path,'rb') as fh:
        zip_sha=hashlib.file_digest(fh,'sha256').hexdigest()
    assert zip_sha==EXPECTED_ZIP_SHA, f'Raw evidence archive changed: {zip_sha}'
    with zipfile.ZipFile(path) as z:
        names=z.namelist()
        assert len(names)==len(set(names)), 'duplicate ZIP entries'
        seen=set()
        for line in z.read('SHA256SUMS.txt').decode('utf-8').splitlines():
            match=re.fullmatch(r'([a-f0-9]{64})  \./(.+)',line)
            assert match, 'invalid SHA256SUMS line'
            want,name=match.groups()
            assert name in names and name not in seen
            seen.add(name)
            assert sha_bytes(z.read(name))==want, 'SHA mismatch: '+name
        assert len(seen)==648, f'wrong hash manifest count {len(seen)}'
        assert set(names)-seen=={'SHA256SUMS.txt','F2P/','P2P/'}, 'unexpected files'
        audit_bytes=z.read('D2_JUNIT_AUDIT.json')
        assert sha_bytes(audit_bytes)==EXPECTED_AUDIT_SHA
        audit=json.loads(audit_bytes)
        assert audit['classification']=='POST_HOC_DIAGNOSTIC_ONLY'
        assert audit['original_a5_r1']=='PATCH_QUALIFICATION_FAIL_NO_RETRY'
        assert audit['diagnostic_patch_sha256']==EXPECTED_PATCH_SHA
        assert audit['physical_invocations_verified']==318
        counts=collections.Counter()
        node_summaries=[]
        for stage,num_nodes in (('F2P',3),('P2P',103)):
            nodes=json.loads(z.read(stage+'/NODES.json'))
            by_node=audit['stages'][stage]['by_node']
            assert len(nodes)==num_nodes and len(set(nodes))==num_nodes
            assert set(nodes)==set(by_node)
            assert audit['stages'][stage]['complete_and_integrity_checked']
            ledger=[json.loads(s) for s in z.read(stage+'/COMMAND_LEDGER.jsonl').decode().splitlines() if s.strip()]
            assert len(ledger)==num_nodes*3
            keys=set()
            for rec in ledger:
                i,repeat=rec['index'],rec['repetition']
                assert 0<=i<num_nodes and 0<=repeat<3
                assert (i,repeat) not in keys
                keys.add((i,repeat))
                node=nodes[i]
                assert rec['node']==node and rec['stage']==stage and not rec['timeout']
                xml_path=f'{stage}/r{repeat}_f{i}.xml'
                log_path=f'{stage}/r{repeat}_f{i}.stdout_stderr.log'
                assert sha_bytes(z.read(xml_path))==rec['xml_sha256']
                assert sha_bytes(z.read(log_path))==rec['log_sha256']
                root=ElementTree.fromstring(z.read(xml_path))
                suites=root.findall('.//testsuite')
                assert len(suites)==1
                suite=suites[0]
                assert int(suite.attrib['tests'])==1
                assert int(suite.attrib['errors'])==0
                assert int(suite.attrib['skipped'])==0
                fail=int(suite.attrib['failures'])
                assert fail in (0,1)
                outcome='FAIL' if fail else 'PASS'
                assert (rec['return_code']==0)==(outcome=='PASS')
                entries=[e for e in by_node[node] if e['repeat']==repeat]
                assert len(entries)==1 and entries[0]['outcome']==outcome
                assert entries[0]['rc']==rec['return_code']
                counts[stage+'_'+outcome]+=1
            assert len(keys)==num_nodes*3
            for n in nodes:
                outcomes=[e['outcome'] for e in by_node[n]]
                assert len(outcomes)==3
                node_summaries.append({'stage':stage,'node':n,'outcomes':outcomes})
        assert counts=={'F2P_PASS':3,'F2P_FAIL':6,'P2P_PASS':309}
        assert audit['f2p_distinct_stable_pass']==1 and audit['p2p_distinct_stable_pass']==103
    return {'verdict':'PASS','raw_zip_sha256':zip_sha,'junit_audit_sha256':EXPECTED_AUDIT_SHA,
        'manifest_files_verified':len(seen),'distinct_nodes':106,'physical_invocations':318,
        'F2P_stable_pass':'1/3','P2P_stable_pass':'103/103','F2P_physical_pass':3,
        'F2P_physical_fail':6,'P2P_physical_pass':309,
        'candidate':'D2_POST_HOC_DIAGNOSTIC_ONLY','original_A5_R1':'STOP'}

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('raw_zip',help='Original T11_D2_RESUME_E2E_20261027T183920378Z.zip')
    args=ap.parse_args()
    try:
        print(json.dumps(verify(args.raw_zip),indent=2,ensure_ascii=False))
    except Exception as exc:
        print('INDEPENDENT_EVIDENCE_AUDIT=STOP:',str(exc),file=sys.stderr)
        sys.exit(1)
