#!/usr/bin/env python3
"""Materialize a declared test-informed D3 repair on a COPY of immutable D2.

Does not claim a new model generation or prospective benchmark success.
"""
from __future__ import annotations
import argparse
import ast
import difflib
import hashlib
import json
import pathlib
import subprocess

SOURCE_SHAS = {
    'saleor/app/installation_utils.py': 'f2bc364b2dde5ba64b0020a89be7a845321fa552e0685ec2174f66817c370224',
    'saleor/app/manifest_validations.py': '7b442c57b450f9c968b0ddd912d163dd374c882fce9dd847ab3d277660374042',
}
# Exact frozen D2 anchors. A mismatch stops; no fuzzy matching or blind substitutions.
TOKEN_BEFORE = '''    _, token = app.tokens.create(name="Default token")  # type: ignore[call-arg] # calling create on a related manager # noqa: E501

    token_target_url = manifest_data.get("tokenTargetUrl")
    if token_target_url:
'''
TOKEN_AFTER = '''    token_target_url = manifest_data.get("tokenTargetUrl")
    token = None
    if token_target_url:
        _, token = app.tokens.create(name="Default token")  # type: ignore[call-arg] # calling create on a related manager # noqa: E501
'''
EXT_BEFORE = '''    # Check if app URL or token target URL is provided
    app_url = manifest_data.get("appUrl")
    token_target_url = manifest_data.get("tokenTargetUrl")

    # Only validate absolute URLs (with protocol)
'''
EXT_AFTER = '''    # A non-APP_PAGE relative extension needs appUrl, not just tokenTargetUrl.
    app_url = manifest_data.get("appUrl")
    token_target_url = manifest_data.get("tokenTargetUrl")
    if (
        extension_url.startswith("/")
        and extension.get("target", DEFAULT_APP_TARGET).lower() != "app_page"
        and not app_url
    ):
        raise ValidationError(
            "Manifest is invalid, appUrl is required for a relative extension URL"
        )

    # Only validate absolute URLs (with protocol)
'''

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def edit_one(src: bytes, needle: str, replacement: str, filename: str) -> bytes:
    if b'\r' in src or not src.endswith(b'\n'):
        raise ValueError(f'STOP_NON_LF_SOURCE:{filename}')
    old, new = needle.encode(), replacement.encode()
    if src.count(old) != 1:
        raise ValueError(f'STOP_D2_ANCHOR_NOT_UNIQUE:{filename}:{src.count(old)}')
    out = src.replace(old, new)
    ast.parse(out.decode('utf8'), filename=filename)
    compile(out, filename, 'exec')
    return out


def construct(a: bytes, b: bytes) -> tuple[bytes, bytes]:
    updated_b = edit_one(b, EXT_BEFORE, EXT_AFTER, 'manifest_validations.py')
    updated_b = edit_one(updated_b,
        '        c) tokenTargetUrl is provided\n',
        '', 'manifest_validations.py_docstring')
    updated_b = edit_one(updated_b,
        "    # Relative URLs (starting with '/') are allowed when appUrl or tokenTargetUrl is provided\n",
        '    # Relative URLs require an APP_PAGE target or a configured appUrl.\n',
        'manifest_validations.py_comment')
    return (edit_one(a, TOKEN_BEFORE, TOKEN_AFTER, 'installation_utils.py'), updated_b)


def selftest():
    a=('def example():\n'+TOKEN_BEFORE+'        try:\n            send_app_token(target_url=token_target_url, token=token)\n        except Exception:\n            raise\n    return token\n').encode()
    b=('def example(extension, manifest_data):\n    """Example\n        c) tokenTargetUrl is provided\n    """\n    extension_url = extension["url"]\n'+EXT_BEFORE+"    # Relative URLs (starting with '/') are allowed when appUrl or tokenTargetUrl is provided\n"+'    return app_url\n').encode()
    x,y=construct(a,b)
    assert b'token = None\n    if token_target_url:\n        _, token' in x
    assert b'and not app_url' in y
    assert x==construct(a,b)[0] and y==construct(a,b)[1]
    try: construct(x,b)
    except ValueError as e: assert 'STOP_D2_ANCHOR_NOT_UNIQUE' in str(e)
    else: raise AssertionError('FAIL_OPEN_ON_REAPPLICATION')
    try: edit_one(a.replace(b'    if token_target_url:', b'    if other_condition:'),TOKEN_BEFORE,TOKEN_AFTER,'x')
    except ValueError: pass
    else: raise AssertionError('FAIL_OPEN_ON_CHANGED_D2')
    # Functional self-tests on isolated, extracted functions (not Saleor/Django).
    import types
    ns = {'DEFAULT_APP_TARGET': 'popup', 'ValidationError': ValueError,
          '_clean_app_url':lambda url: None}
    extension_fn='def validate(extension, manifest_data):\n    extension_url=extension["url"]\n'+EXT_AFTER+'    if not extension_url.startswith("/"):\n        _clean_app_url(extension_url)\n'
    exec(compile(extension_fn, '<D3-validation-selftest>', 'exec'), ns)
    tests=[({'url':'/x','target':'new_tab'},{'appUrl':None,'tokenTargetUrl':'https://token'},True),
           ({'url':'/x','target':'new_tab'},{'appUrl':'https://app'},False),
           ({'url':'/x','target':'app_page'},{'appUrl':None},False),
           ({'url':'https://site','target':'new_tab'},{'appUrl':None,'tokenTargetUrl':'https://token'},False)]
    for ext,manifest,must_raise in tests:
        try:ns['validate'](ext,manifest)
        except ValueError:assert must_raise
        else:assert not must_raise
    # Repository-less git apply positive and negative fixture.
    import tempfile
    with tempfile.TemporaryDirectory(prefix='t11_d3_nogit_selftest_') as td:
        root=pathlib.Path(td)
        source_file=root/'example.py'
        source_file.write_bytes(a)
        patch=''.join(['diff --git a/example.py b/example.py\n'] + list(
            difflib.unified_diff(a.decode().splitlines(keepends=True),
                                 x.decode().splitlines(keepends=True),
                                 fromfile='a/example.py', tofile='b/example.py')))
        patch_file=root/'change.patch'
        patch_file.write_text(patch,encoding='utf8')
        assert not (root/'.git').exists()
        assert subprocess.run(['git','apply','--check',str(patch_file)],cwd=root,capture_output=True).returncode==0
        assert subprocess.run(['git','apply',str(patch_file)],cwd=root,capture_output=True).returncode==0
        assert source_file.read_bytes()==x
        assert subprocess.run(['git','apply','--check',str(patch_file)],cwd=root,capture_output=True).returncode!=0
        assert subprocess.run(['git','apply','--reverse','--check',str(patch_file)],cwd=root,capture_output=True).returncode==0
    print('D3_REPAIR_UNIT_SELFTEST=PASS; NOT_SALEOR_BEHAVIORAL_EVIDENCE')


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--selftest',action='store_true')
    p.add_argument('--worktree',type=pathlib.Path)
    p.add_argument('--evidence',type=pathlib.Path)
    args=p.parse_args()
    if args.selftest:
        selftest(); return
    if not args.worktree or not args.evidence: p.error('--worktree and --evidence required')
    wt=args.worktree; evidence=args.evidence
    if evidence.exists():raise SystemExit('STOP_D3_EVIDENCE_EXISTS')
    old={}
    for name,expected in SOURCE_SHAS.items():
        f=wt/name
        old[name]=f.read_bytes()
        if sha(old[name])!=expected:raise SystemExit('STOP_D2_SOURCE_SHA_DRIFT:'+name)
    new1,new2=construct(old[list(SOURCE_SHAS)[0]],old[list(SOURCE_SHAS)[1]])
    new=dict(zip(SOURCE_SHAS,(new1,new2)))
    delta=[]
    for name in SOURCE_SHAS:
        diff=list(difflib.unified_diff(old[name].decode().splitlines(keepends=True),new[name].decode().splitlines(keepends=True),
          fromfile='a/'+name,tofile='b/'+name))
        if not diff:raise SystemExit('STOP_D3_NO_DIFF:'+name)
        delta.extend(['diff --git a/'+name+' b/'+name+'\n']+diff)
    difftext=''.join(delta)
    evidence.mkdir(parents=True,mode=0o700)
    (evidence/'D3_OVER_D2.patch').write_text(difftext,encoding='utf8',newline='\n')
    patch_sha=sha(difftext.encode())
    # STAGE IS A FILE SNAPSHOT, NOT A GIT REPOSITORY.  git diff --check
    # returns 129 for a repository-less snapshot, regardless of patch validity.
    # Verify applicability and whitespace before modifying the disposable COPY.
    patch_file = evidence/'D3_OVER_D2.patch'
    for line in difftext.splitlines():
        if line.startswith('+') and not line.startswith('+++') and line.rstrip(' \t') != line:
            raise SystemExit('STOP_D3_PATCH_TRAILING_WHITESPACE')
    for args in (['git','apply','--check',str(patch_file)],
                 ['git','apply',str(patch_file)]):
        process = subprocess.run(args, cwd=wt, text=True,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if process.returncode:
            raise SystemExit('STOP_D3_GIT_APPLY_RC_'+str(process.returncode)+':'+process.stderr[:400])
    actual={name:sha((wt/name).read_bytes()) for name in SOURCE_SHAS}
    if actual!={name:sha(b) for name,b in new.items()}:raise SystemExit('STOP_D3_POST_APPLY_SHA')
    reverse = subprocess.run(['git','apply','--reverse','--check',str(patch_file)],cwd=wt,
                             text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if reverse.returncode:
        raise SystemExit('STOP_D3_REVERSE_APPLY_CHECK_RC_'+str(reverse.returncode))
    (evidence/'EXPECTED_D3_SOURCE_SHA256.json').write_text(json.dumps(actual,indent=2,sort_keys=True)+'\n')
    receipt={'schema':'t11_d3_test_informed_repair_v1','candidate':'D3_TEST_INFORMED_REPAIR_CONTROL',
            'original_model_A5_R1':'STOP','source_D2_SHA256':SOURCE_SHAS,
            'd3_source_sha256':actual,'d3_over_d2_patch_sha256':patch_sha,
            'edits':['conditional default-token creation','reject non-APP_PAGE relative URL if appUrl absent'],
            'model_api_calls_for_repair':0,'research_validity':'TEST_INFORMED_REPAIR_NOT_MODEL_PASS_AT_1'}
    (evidence/'D3_REPAIR_RECEIPT.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    print('D3_REPAIR_CONTROL_CREATED=PASS; MODEL_A5_R1=STOP')
    print('D3_INCREMENTAL_PATCH_SHA256='+patch_sha)
    for k,v in actual.items():print('D3_SOURCE_SHA256 '+k+' '+v)

if __name__=='__main__':main()
