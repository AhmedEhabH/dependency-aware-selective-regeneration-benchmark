#!/usr/bin/env python3
"""Immutable additional D3-R3 milestone publication; never overwrite earlier protocol/STOP."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

BRANCH = 'research/track-1-1-generated-e2e-2026-10-27'
TARGET = 'evidence/track-1-1/generated-code-e2e/2026-10-27'
REMOTE_RE = re.compile(r'^(https://github\.com/|git@github\.com:)AhmedEhabH/dependency-aware-selective-regeneration-benchmark(\.git)?$')
OLD_STOP_MARKER = '## D3 REPAIR CONTROL RESULT (2026-10-27)'
PRE_MARKER = '## D3 R2 EVALUATOR HASH-PIN CORRECTION (2026-10-27)'
R3_PRE_MARKER = '## D3 R3 NON-REPOSITORY PATCH APPLICATION CORRECTION (2026-10-28)'
POST_MARKER = '## D3 R3 REAL BEHAVIORAL RESULT (2026-10-28)'


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(repo: Path, *argv: str) -> str:
    r = subprocess.run(['git', '-C', str(repo), *argv], capture_output=True,
                       text=True, encoding='utf8', errors='replace', check=False)
    if r.returncode:
        raise RuntimeError(f'STOP_GIT_{argv[0]}_RC_{r.returncode}: {r.stderr[:500]}')
    return r.stdout.strip()


def receipt_check(kit: Path):
    manifest = kit/'SHA256SUMS.txt'
    if not manifest.is_file(): raise RuntimeError('STOP_KIT_MANIFEST_MISSING')
    rows = manifest.read_text(encoding='ascii').splitlines()
    names = set()
    for line in rows:
        match = re.fullmatch(r'([0-9a-f]{64})  ([A-Za-z0-9_.-]+)', line)
        if match is None: raise RuntimeError('STOP_MANIFEST_INVALID_LINE')
        h, name = match.groups()
        if name in names or not (kit/name).is_file() or digest(kit/name)!=h:
            raise RuntimeError('STOP_KIT_SHA_OR_DUPLICATE:'+name)
        names.add(name)
    expected = {p.name for p in kit.iterdir() if p.is_file()}-{'SHA256SUMS.txt'}
    if names!=expected: raise RuntimeError('STOP_KIT_MANIFEST_INCOMPLETE')
    sh = (kit/'T11_D3_E2E_R3_FROM_HASHED_CACHE.sh').read_text()
    builder = digest(kit/'T11_D3_CREATE_CONTROL.py')
    if builder != '0ca54687f0cd1529e3e5eb781eef59b6e006a716ef9c5de6453bc9301dce947b':
        raise RuntimeError('STOP_UNEXPECTED_BUILDER_IDENTITY')
    needle = f'EQ "$KIT/T11_D3_CREATE_CONTROL.py" \'{builder}\''
    if sh.count(needle)!=1 or '2736b630c55f465d3de0d879e0540b74c1e9412855c05764537b3663a8078966' in sh:
        raise RuntimeError('STOP_RUNNER_HASH_PIN_INCONSISTENT')


def publish(repo: Path, kit: Path, phase: str, public: Path|None, results: Path|None,
            test_fixture_remote: bool=False):
    receipt_check(kit)
    if not (repo/'.git').exists():raise RuntimeError('STOP_LOCAL_GIT_CLONE_MISSING')
    if git(repo,'branch','--show-current')!=BRANCH:raise RuntimeError('STOP_WRONG_GIT_BRANCH')
    remote=git(repo,'remote','get-url','origin')
    if not test_fixture_remote and not REMOTE_RE.fullmatch(remote):
        raise RuntimeError('STOP_UNEXPECTED_REMOTE')
    if git(repo,'status','--porcelain'):
        raise RuntimeError('STOP_DIRTY_WORKTREE_BEFORE_PUBLISH')
    local=git(repo,'rev-parse','HEAD')
    remote_line=git(repo,'ls-remote','--exit-code','origin','refs/heads/'+BRANCH)
    if not remote_line or remote_line.split()[0]!=local:
        raise RuntimeError('STOP_REMOTE_HEAD_MOVED')
    target=repo/TARGET
    if not (target/'PROGRESS.md').is_file() or not (target/'D3_PUBLIC_SUMMARY.json').is_file():
        raise RuntimeError('STOP_EARLIER_D3_STOP_NOT_RECORDED')
    oldstatus=json.loads((target/'D3_PUBLIC_SUMMARY.json').read_text())
    if oldstatus.get('status')!='INFRASTRUCTURE_STOP_BEFORE_REPAIR':
        raise RuntimeError('STOP_PREVIOUS_RESULT_NOT_EXPECTED_STOP')
    prog=target/'PROGRESS.md'; existing=prog.read_text(encoding='utf8')
    if OLD_STOP_MARKER not in existing:raise RuntimeError('STOP_PREVIOUS_PROGRESS_MISSING')
    if phase=='correction':
        if PRE_MARKER not in existing:raise RuntimeError('STOP_R2_CORRECTION_MILESTONE_MISSING')
        if R3_PRE_MARKER in existing:raise RuntimeError('STOP_R3_PREPUB_ALREADY_EXISTS')
        sources={name:kit/name for name in (
            'D3_R3_RUNNER_CORRECTION.md','T11_D3_CREATE_CONTROL.py',
            'T11_D3_E2E_R3_FROM_HASHED_CACHE.sh','T11_D3_R3_PUBLISH.py')}
        summary=f'''{R3_PRE_MARKER}\n\n- R2 host run on 2026-10-28 stopped before pytest: copied D2 stage was not a Git repository; `git diff --check` exited 129. This is an evaluator fault, not a Saleor test result.\n- R2 result publication STOPPED because a partially produced D3 patch had no valid completion receipt; raw partial patch was not published. Prior R2 correction and previous STOP evidence stay immutable.\n- R3 builder uses repository-independent `git apply --check`, `git apply`, reverse applicability, exact source SHA, syntax and scope verification before accepting D3.\n- Frozen test nodes, D2 inputs, D3 *semantic edits*, hashed offline dependencies, original A5-R1 STOP, and zero new model calls unchanged.\n- R3 evaluator published prior to behavioral replay.\n'''
        message='protocol(track1.1): fix repository-less D3 patch application and STOP publication'
    else:
        if R3_PRE_MARKER not in existing:raise RuntimeError('STOP_R3_PREPUB_NOT_RECORDED')
        if POST_MARKER in existing:raise RuntimeError('STOP_R2_RESULT_ALREADY_EXISTS')
        if public is None or results is None:raise RuntimeError('STOP_RESULT_ARGS')
        data_path=public/'D3_PUBLIC_SUMMARY.json'; md_path=public/'D3_PUBLIC_SUMMARY.md'
        if not data_path.is_file() or not md_path.is_file():raise RuntimeError('STOP_MISSING_SAFE_SUMMARY')
        data=json.loads(data_path.read_text())
        if data.get('classification')!='TEST_INFORMED_REPAIR_CONTROL_NOT_MODEL_PASS_AT_1' or data.get('official_A5_R1')!='STOP':
            raise RuntimeError('STOP_PUBLIC_SCHEMA_OR_PROVENANCE')
        allowed={'D3_COMPLETE_CONTROL_PASS','D3_COMPLETE_CONTROL_FUNCTIONAL_FAIL',
            'D3_F2P_FUNCTIONAL_FAIL_P2P_NOT_RUN','D3_F2P_EVIDENCE_STOP',
            'D3_AUDIT_INTEGRITY_STOP','D3_EXECUTION_STOP_BEFORE_FINAL_AUDIT',
            'INFRASTRUCTURE_STOP_BEFORE_REPAIR'}
        if data.get('status') not in allowed:raise RuntimeError('STOP_UNSUPPORTED_STATUS')
        sources={'D3_R3_PUBLIC_SUMMARY.json':data_path,'D3_R3_PUBLIC_SUMMARY.md':md_path}
        patch=results/'D3_STAGE/D3_OVER_D2.patch'
        if patch.is_file() and data.get('d3_repair_patch_sha256'):
            expected=['a/saleor/app/installation_utils.py b/saleor/app/installation_utils.py',
                      'a/saleor/app/manifest_validations.py b/saleor/app/manifest_validations.py']
            headers=re.findall(r'^diff --git (.+)$',patch.read_text(),re.MULTILINE)
            if headers!=expected or digest(patch)!=data.get('d3_repair_patch_sha256'):
                raise RuntimeError('STOP_PATCH_SCOPE_OR_HASH')
            sources['D3_R3_OVER_D2.patch']=patch
        q=results/'D3_QUALITY_REPORT.json'
        if q.is_file():
            qual=json.loads(q.read_text());
            if qual.get('classification')!='TEST_INFORMED_REPAIR_CONTROL_NOT_PROSPECTIVE_MODEL_GENERATION':
                raise RuntimeError('STOP_UNTRUSTED_QUALITY_REPORT')
            if qual.get('frozen_original_A5_R1')!='STOP':raise RuntimeError('STOP_QUALITY_A5')
            if qual.get('code_identity',{}).get('d3_over_d2_sha256')!=data.get('d3_repair_patch_sha256'):
                raise RuntimeError('STOP_QUALITY_CODE_IDENTITY')
            sources['D3_R3_QUALITY_REPORT.json']=q
        st=data['status']
        summary=f'''{POST_MARKER}\n\n- R2 repository-less `git diff --check` STOP and R2 result publication STOP are preserved separately in R3 correction milestone.\n- Original first D3 attempt remains `INFRASTRUCTURE_STOP_BEFORE_REPAIR`. R3 corrects repository-less patch validation only; D3 semantic edits remain unchanged.\n- **R3 run verdict:** `{st}`; D3 test-informed control, never independent model pass@1.\n- F2P stable: `{data.get('f2p_stable_pass')}/3`; P2P stable: `{data.get('p2p_stable_pass')}/103`; full verified physical invocations: `{data.get('verified_invocations')}`.\n- Public summary, bounded quality metrics and D3 patch, if generated, are sanitized. Raw JUnit/logs and tokens stay on the host.\n- Original A5-R1 remains STOP; D2 remains frozen 1/3 F2P and 103/103 P2P.\n'''
        message='evidence(track1.1): publish independent D3 R3 gated E2E outcome'
    for name,source in sources.items():
        if not source.is_file() or (target/name).exists():
            raise RuntimeError('STOP_PUBLIC_FILE_MISSING_OR_OVERWRITE:'+name)
    # After all preconditions pass, publish only explicit allowlisted files.
    for name,source in sources.items():shutil.copyfile(source,target/name)
    with prog.open('a',encoding='utf8',newline='\n') as f:f.write('\n'+summary.rstrip()+'\n')
    paths=[TARGET+'/PROGRESS.md']+[TARGET+'/'+n for n in sources]
    git(repo,'-c','core.autocrlf=false','add','--',*paths)
    git(repo,'diff','--cached','--check')
    git(repo,'commit','-m',message)
    git(repo,'push','origin','HEAD:refs/heads/'+BRANCH)
    print('D3_R3_GITHUB_'+phase.upper()+'_PUSH=PASS')
    print('D3_R3_GITHUB_COMMIT='+git(repo,'rev-parse','HEAD'))


def main():
    p=argparse.ArgumentParser()
    p.add_argument('phase',choices=['correction','result'])
    p.add_argument('--repo',type=Path,required=True)
    p.add_argument('--kit',type=Path,required=True)
    p.add_argument('--public',type=Path)
    p.add_argument('--results',type=Path)
    p.add_argument('--test-fixture-remote',action='store_true')
    a=p.parse_args()
    publish(a.repo,a.kit,a.phase,a.public,a.results,a.test_fixture_remote)

if __name__=='__main__':main()
