#!/usr/bin/env bash
# EVALUATOR ONLY, not visible to generator. No model calls, no Docker start.
# Verifies a generated LF diff against the frozen NEG Git tree and stages a clean copy.
set -euo pipefail
if [ "$#" -ne 4 ]; then echo 'USAGE: T11_STAGE_A5_GIT_LF.sh PATCH_LINUX_PATH PATCH_SHA256 EXPECTED_SOURCE_LF_SHA_JSON NEW_EMPTY_RECEIPT_DIR' >&2; exit 2; fi
PATCH="$1"; PIN="$2"; EXPECT="$3"; OUT="$4"
BARE='/mnt/d/wp2_env_store/git_cache/saleor.git'
ALT='/root/M19B_R6_TREE_RECOVERY_20261026T202446Z_774e6f0e/objects'
NEG='65cd0b6e07e73c102ae600fea0fabea827b7fe29'
PARENT='798632158394c9f2911e6d36e8e424fd55007dc4'
A='saleor/app/installation_utils.py'; B='saleor/app/manifest_validations.py'
A_LF='a78a6a58128c1e0e04d94db5a418997f168a3ae8330eae868934dbbcbad297c0'
B_LF='b1743317be065d7a5f8614a6ab389da783b2c3b3cdf1a27b716c9fdf0338881d'
[[ "$(id -u)" == '0' ]] || { echo 'STOP_ROOT_REQUIRED_FOR_ALTERNATE_OBJECT_STORE'; exit 3; }
[[ -f "$PATCH" && -f "$EXPECT" && -d "$ALT" && -d "$BARE" ]] || { echo 'STOP_REQUIRED_SOURCE_MISSING'; exit 4; }
[[ "$PIN" =~ ^[0-9a-f]{64}$ ]] || { echo 'STOP_PATCH_SHA_BAD_FORMAT'; exit 5; }
[[ "$(sha256sum "$PATCH" | cut -d' ' -f1)" == "$PIN" ]] || { echo 'STOP_PATCH_HASH_MISMATCH'; exit 6; }
[[ ! -e "$OUT" ]] || { echo 'STOP_RECEIPT_PATH_ALREADY_EXISTS'; exit 7; }
export GIT_ALTERNATE_OBJECT_DIRECTORIES="$ALT"
[[ "$(git --git-dir="$BARE" cat-file -t "$PARENT")" == commit ]] || { echo 'STOP_PARENT_NOT_PRESENT'; exit 8; }
[[ "$(git --git-dir="$BARE" cat-file -t "$NEG")" == tree ]] || { echo 'STOP_NEG_NOT_PRESENT'; exit 9; }
# patch must be a UTF-8 LF unified diff, with no CRLF context mismatch.
python3 - "$PATCH" <<'PY'
import pathlib,sys
b=pathlib.Path(sys.argv[1]).read_bytes()
if not b.startswith(b'diff --git a/saleor/app/') or b'\r' in b:
    raise SystemExit('STOP_NOT_CANONICAL_LF_GIT_DIFF')
for line in b.split(b'\n'):
    if line.startswith(b'diff --git '):
        words=line.decode('utf-8').split()
        allowed={'saleor/app/installation_utils.py','saleor/app/manifest_validations.py'}
        if len(words)!=4 or words[2][2:] not in allowed or words[3][2:]!=words[2][2:]:
            raise SystemExit('STOP_PATCH_OUT_OF_SCOPE')
PY
ROOT="$(mktemp -d /root/t11_a5_eval_XXXXXXXX)"
WT="$ROOT/wt"; mkdir -p "$WT"
# preserve failing roots for forensic review; never clean/overwrite shared Git branches.
git --git-dir="$BARE" archive "$NEG" | tar -xf - -C "$WT"
[[ "$(sha256sum "$WT/$A" | cut -d' ' -f1)" == "$A_LF" ]] || { echo 'STOP_NEG_A_SOURCE_HASH_MISMATCH'; exit 10; }
[[ "$(sha256sum "$WT/$B" | cut -d' ' -f1)" == "$B_LF" ]] || { echo 'STOP_NEG_B_SOURCE_HASH_MISMATCH'; exit 11; }
mkdir -p "$OUT"
(
  cd "$WT"
  git apply --check "$PATCH" >"$OUT/GIT_APPLY_CHECK.log" 2>&1 || { echo 'STOP_GIT_APPLY_CHECK_FAILED'; exit 12; }
  git apply "$PATCH" >"$OUT/GIT_APPLY.log" 2>&1 || { echo 'STOP_GIT_APPLY_FAILED'; exit 13; }
  python3 - <<'PY'
import ast,pathlib
for p in ('saleor/app/installation_utils.py','saleor/app/manifest_validations.py'):
    ast.parse(pathlib.Path(p).read_bytes(), filename=p)
print('AST_GENERATED_SOURCE=PASS')
PY
)
python3 - "$WT" "$EXPECT" <<'PY2'
import json,hashlib,pathlib,sys
wt=pathlib.Path(sys.argv[1]); e=json.loads(pathlib.Path(sys.argv[2]).read_text('utf-8'))
expected={'saleor/app/installation_utils.py','saleor/app/manifest_validations.py'}
if set(e)!=expected or any(not isinstance(v,str) or len(v)!=64 for v in e.values()):
 raise SystemExit('STOP_GENERATED_SOURCE_SHA_SCHEMA')
for p in expected:
 actual=hashlib.sha256((wt/p).read_bytes()).hexdigest()
 if actual!=e[p]:raise SystemExit('STOP_GENERATED_SOURCE_SHA_MISMATCH: '+p)
print('TWO_GENERATED_SOURCE_SHA=PASS')
PY2
sha256sum "$WT/$A" "$WT/$B" >"$OUT/GENERATED_LF_SOURCE_SHA256.txt"
{
  echo 'SCHEMA=t11_a5_eval_stage_v1'
  echo "FROZEN_PARENT_COMMIT=$PARENT"
  echo "FROZEN_NEG_TREE_OID=$NEG"
  echo "GENERATED_PATCH_SHA256=$PIN"
  echo "STAGE_ROOT=$ROOT"
  echo "EVALUATOR_WORKTREE=$WT"
  echo 'GIT_LF_APPLY_AND_AST=PASS'
  echo 'F2P=NOT_RUN'
  echo 'P2P=NOT_RUN'
  echo 'EGRESS_CONTAINER_AND_DB_QUALIFICATION=PENDING'
} | tee "$OUT/A5_STAGE_RECEIPT.txt"
echo 'NEXT_GATE=EVALUATOR_ONLY_DOCKER_DB_EGRESS_VERIFICATION_BEFORE_TESTS'
