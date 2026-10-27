#!/usr/bin/env python3
"""Offline post-hoc A3 diagnostic ONLY; prints a failed syntax gate, no patches saved.
Never reinterpret this diagnostic as patch qualification under the frozen A3 protocol.
"""
import ast,hashlib,json,pathlib
HERE=pathlib.Path(__file__).resolve().parent
SOURCE=HERE.parent/'GENERATOR_ONLY'/'PARENT_ONLY_SOURCE_REQUEST.json'
RAW=HERE/'A3_ORIGINAL_MODEL_TEXT.txt'
SRC_EXPECT='719392bc4af73272c159bc98fa8ed12fd22ffaaaf53cbcd466d5358cc89721ca'
RAW_EXPECT='9d0a9ad13d530f2ce583dd8705a273f7e63555e568a977f1b65cad51696b080f'
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(SOURCE.read_bytes())==SRC_EXPECT
assert sha(RAW.read_bytes())==RAW_EXPECT
req=json.loads(SOURCE.read_bytes());edits=json.loads(RAW.read_bytes())['edits'];text=req['messages'][1]['content']
original={};work={}
for p in ['saleor/app/installation_utils.py','saleor/app/manifest_validations.py']:
    orig=text.split(f'===== BEGIN PARENT SOURCE: {p} =====\n',1)[1].split(f'\n===== END PARENT SOURCE: {p} =====',1)[0]
    original[p]=orig;work[p]=orig
for ix,e in enumerate(edits):
    p=e['path'];old=e['old'].replace('\r\n','\n').replace('\r','\n').replace('\n','\r\n')
    new=e['new'].replace('\r\n','\n').replace('\r','\n').replace('\n','\r\n')
    current=work[p];occ=current.count(old)
    pos=0;full=[]
    while True:
        k=current.find(old,pos)
        if k<0:break
        start=current.rfind('\n',0,k)+1;end=current.find('\n',k)
        if end<0:end=len(current)
        line=current[start:end].rstrip('\r')
        if line.strip()==old.strip() and k==start+len(line)-len(line.lstrip()):full.append(k)
        pos=k+1
    print(f'EDIT_{ix}_A3_SUBSTRING_OCCURRENCES={occ}; FULL_LINE_MATCHES={len(full)}')
    if occ==1:
        k=current.find(old)
    else:
        assert len(full)==1,'Even post-hoc exact-line diagnostic is ambiguous'
        k=full[0]
    work[p]=current[:k]+new+current[k+len(old):]
for p in work:
    try:ast.parse(work[p],filename=p)
    except SyntaxError as exc:
        print('POST_HOC_LINE_MATCH_AST=FAIL; FILE='+p+'; LINE='+str(exc.lineno)+'; DETAIL='+str(exc.msg))
    else:print('POST_HOC_LINE_MATCH_AST=PASS; FILE='+p)
print('A3_FROZEN_STATUS=PATCH_QUALIFICATION_FAIL')
print('NO_PATCH_SAVED_NO_API_NO_E2E')
