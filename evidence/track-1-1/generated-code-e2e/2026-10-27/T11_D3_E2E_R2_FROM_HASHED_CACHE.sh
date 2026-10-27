#!/usr/bin/env bash
# Track 1.1 D3 test-informed engineering control E2E on exact hashed uv.lock artifacts, offline measurement.
set -Eeuo pipefail
umask 077
[[ $# -eq 3 ]] || { echo 'STOP_USAGE_D3_KIT_PREP_FRESH_RESULTS' >&2; exit 2; }
KIT=$1; PREP=$2; OUT=$3
[[ "$KIT" == /mnt/d/WP2/audit_results/* && "$PREP" == /mnt/d/WP2/audit_results/* && "$OUT" == /mnt/d/WP2/audit_results/* ]] || { echo STOP_SCOPE; exit 3; }
[[ -d "$KIT" && -d "$PREP" && ! -e "$OUT" ]] || { echo STOP_MISSING_INPUT_OR_RESULTS_ALREADY_EXISTS; exit 4; }
IMAGE='sha256:a6e743589b60a4c15676eece07f52ed8347dc501bc782cc53ddffb7200d06c4c'
LOCK_SHA='a4c21a2deb52e20e52b691857fd5adae8f130e6844626c18b3aaebc688eb2d66'
STAGE='/root/t11_a5_eval_cwyoJ15q/wt'
S1='f2bc364b2dde5ba64b0020a89be7a845321fa552e0685ec2174f66817c370224'
S2='7b442c57b450f9c968b0ddd912d163dd374c882fce9dd847ab3d277660374042'
T1='saleor/app/installation_utils.py'; T2='saleor/app/manifest_validations.py'
HASH(){ sha256sum "$1" | cut -d' ' -f1; }
EQ(){ [[ "$(HASH "$1")" == "$2" ]] || { echo "STOP_HASH_DRIFT:$1"; exit 5; }; }
[[ -s "$PREP/PREP_PASS.json" && -s "$PREP/FROZEN_DEV_HASHED.txt" ]] || { echo STOP_PREPARATION_NOT_QUALIFIED; exit 6; }
EQ "$STAGE/uv.lock" "$LOCK_SHA"; EQ "$STAGE/$T1" "$S1"; EQ "$STAGE/$T2" "$S2"
EQ "$KIT/R7_FROZEN_NODES.json" 'f547b88af226ba8ed0c1745c77bf6b90b1f12f5d2e715013c47234e4fcd98cf9'
EQ "$KIT/R8_FROZEN_NODES.json" 'd3392709e5b6a62dd885fc9a29845888259285542a622bb78687f9ff4bfea9a0'
EQ "$KIT/T11_RUN_TEST_NODES_IN_CONTAINER.py" '77a722ee00630f1430fddf9dd3891eafd25e00c83c619d63ee6aa6cb4d50317c'
EQ "$KIT/T11_D3_AUDIT_106.py" 'b2fef9796a26a9dc77e3a6c28edd54722940f3013a4ffe9a505a6ca73f2faa34'
EQ "$KIT/T11_D3_CREATE_CONTROL.py" '2736b630c55f465d3de0d879e0540b74c1e9412855c05764537b3663a8078966'
EQ "$KIT/T11_D3_F2P_GATE.py" 'f8b43b314056d1a6ba72042f10e173647fd7063e8e571bd91b243a7f26a9ce3e'
EQ "$KIT/T11_D3_QUALITY_REPORT.py" '309ae400c8ba3cc02787b5842e4dd4847452c4c7893a006bd45859d566464275'
[[ "$(docker image inspect "$IMAGE" --format '{{.Id}}' 2>/dev/null)" == "$IMAGE" ]] || { echo STOP_IMAGE; exit 7; }
docker image inspect 'postgres:15-alpine' >/dev/null || { echo STOP_PG_IMAGE; exit 7; }
# Fail-closed exact preparation receipt, cache must live under the private WSL root.
CACHE=$(python3 - "$PREP/PREP_PASS.json" "$PREP/FROZEN_DEV_HASHED.txt" "$LOCK_SHA" "$IMAGE" <<'PY_CHECK'
import json,sys,pathlib,hashlib
p,req,lock,image=sys.argv[1:]
j=json.load(open(p))
assert j['status']=='OFFLINE_LOCKED_CLOSURE_PASS'
assert j['original_a5_r1']=='STOP' and j['candidate']=='D2_POST_HOC_ONLY'
assert j['uv_lock_sha256']==lock and j['oci_image']==image
assert j['network_in_offline_smoke']=='none'
assert hashlib.sha256(pathlib.Path(req).read_bytes()).hexdigest()==j['hashed_requirements_sha256']
c=j['cache_wsl_path']; assert c.startswith('/root/t11_d2_hydrated_') and c.endswith('/cache')
assert pathlib.Path(c).is_dir() and any(pathlib.Path(c).iterdir())
assert 'FROZEN_HASHED_OFFLINE_CLOSURE_PASS' in pathlib.Path(p).with_name('OFFLINE_SMOKE.log').read_text()
print(c)
PY_CHECK
) || { echo STOP_PREP_RECEIPT; exit 8; }
[[ -n "$CACHE" ]] || { echo STOP_CACHE_EMPTY; exit 8; }
python3 "$KIT/VERIFY_HASHED_EXPORT.py" "$PREP/FROZEN_DEV_HASHED.txt" "$KIT/FROZEN_DEV_EXPORT_REFERENCE.txt" "$PREP/E2E_EXPORT_AUDIT.json" || { echo STOP_LOCKED_REQUIREMENTS; exit 9; }
# Confirm exactly 106 frozen distinct test nodes, unchanged from original kit.
python3 - "$KIT/R7_FROZEN_NODES.json" "$KIT/R8_FROZEN_NODES.json" "$STAGE" <<'PY_NODES'
import json,pathlib,sys
p,q,root=sys.argv[1:];a=json.loads(pathlib.Path(p).read_text());b=json.loads(pathlib.Path(q).read_text())
assert len(a)==3 and len(b)==103 and len(set(a))==3 and len(set(b))==103 and not set(a)&set(b)
for node in a+b:
 path,fn=node.split('::',1);testname=fn.split('[',1)[0].split('::')[-1]
 assert testname in pathlib.Path(root,path).read_text(errors='replace'),f'NODE_NOT_IN_FROZEN_TEST_SOURCE:{node}'
print('FROZEN_NODES=106_DISTINCT_PASS')
PY_NODES
MEM=$(awk '/MemAvailable:/{print $2}' /proc/meminfo)
DISK=$(df -Pk /mnt/d | awk 'NR==2{print $4}')
[[ "$MEM" -ge 6291456 && "$DISK" -ge 52428800 ]] || { echo STOP_RESOURCE_GUARD; exit 10; }
TAG="$(date -u +%Y%m%dT%H%M%SZ)_$(od -An -N5 -tx1 /dev/urandom | tr -d ' \n')"
ROOT="/root/t11_d3_measured_${TAG}"
NET="t11-d3-control-${TAG//_/-}"
PG="t11-d3-postgres-${TAG//_/-}"
DB="t11d3_$(od -An -N6 -tx1 /dev/urandom | tr -d ' \n')"
mkdir -m 700 "$OUT"; mkdir -m 700 "$ROOT"
START=$(date +%s); NETWORK_CREATED=0; PG_CREATED=0
CLEANUP(){
 local rc=$?; trap - EXIT
 if [[ "$PG_CREATED" == 1 ]];then docker logs "$PG" >"$OUT/postgres.log" 2>&1 || true;docker rm -f "$PG" >/dev/null 2>&1 || true;fi
 if [[ "$NETWORK_CREATED" == 1 ]];then docker network rm "$NET" >/dev/null 2>&1 || true;fi
 rm -f "$ROOT/db.env" "$ROOT/eval.env"
 if [[ "$ROOT" == /root/t11_d3_measured_* && -d "$ROOT" ]]; then
   rm -rf -- "$ROOT"
   echo 'EPHEMERAL_D3_WORKTREE_CLEANED=YES; ORIGINAL_D2_STAGING_NOT_TOUCHED' | tee -a "$OUT/EXECUTION_METADATA.txt"
 fi
 echo "FINAL_STATUS_RC=$rc" | tee -a "$OUT/EXECUTION_METADATA.txt"
 echo "RESULTS_BYTES=$(du -sb "$OUT" | cut -f1)" | tee -a "$OUT/EXECUTION_METADATA.txt"
 echo "FINAL_WALL_SECONDS=$(($(date +%s)-START))" | tee -a "$OUT/EXECUTION_METADATA.txt"
 echo 'ORIGINAL_A5_R1=STOP; CANDIDATE=D3_TEST_INFORMED_REPAIR_CONTROL; MODEL_API_CALLS=0' | tee -a "$OUT/EXECUTION_METADATA.txt"
 (cd "$OUT" && find . -type f ! -name SHA256SUMS.txt -print0 | sort -z | xargs -0 -r sha256sum > SHA256SUMS.txt) || true
 exit "$rc"
}
trap CLEANUP EXIT
cp -a "$STAGE" "$ROOT/wt_t"
EQ "$ROOT/wt_t/uv.lock" "$LOCK_SHA";EQ "$ROOT/wt_t/$T1" "$S1";EQ "$ROOT/wt_t/$T2" "$S2"
# Engineer-declared D3 control changes only the COPY. Never mutate the D2 staging tree.
python3 "$KIT/T11_D3_CREATE_CONTROL.py" --worktree "$ROOT/wt_t" --evidence "$OUT/D3_STAGE"
cp "$OUT/D3_STAGE/EXPECTED_D3_SOURCE_SHA256.json" "$ROOT/expected.json"
read -r D3S1 D3S2 < <(python3 - "$ROOT/expected.json" <<'PY_D3_HASHES'
import json,sys
j=json.load(open(sys.argv[1]))
print(j['saleor/app/installation_utils.py'],j['saleor/app/manifest_validations.py'])
PY_D3_HASHES
)
[[ ${#D3S1} == 64 && ${#D3S2} == 64 ]] || { echo STOP_D3_HASHES;exit 11; }
EQ "$ROOT/wt_t/$T1" "$D3S1";EQ "$ROOT/wt_t/$T2" "$D3S2"
# The original stage is still D2 (immutable), and the new control is a distinct copy.
EQ "$STAGE/$T1" "$S1";EQ "$STAGE/$T2" "$S2"
{
  echo 'SCHEMA=t11_d3_test_informed_106_hashed_cache_v1'
  echo "UTC_START=$(date -u +%FT%TZ)"
  echo 'A5_R1_ORIGINAL=STOP; D2_FROZEN=YES; D3_TEST_INFORMED_REPAIR_CONTROL=YES'
  echo "PINNED_OCI_IMAGE=$IMAGE; PINNED_LOCK_SHA256=$LOCK_SHA"
  echo "HASHED_REQUIREMENTS_SHA256=$(HASH "$PREP/FROZEN_DEV_HASHED.txt")"
  echo "PREP_PASS_SHA256=$(HASH "$PREP/PREP_PASS.json")"
  echo 'NETWORK_PREPARATION=ONLINE_SEPARATE_NON_MEASUREMENT; NETWORK_MEASUREMENT=DOCKER_INTERNAL_OFFLINE'
  echo "RAM_AVAILABLE_KIB=$MEM; D_DISK_AVAILABLE_KIB=$DISK"
  echo "DB=$DB; PG_CONTAINER=$PG; NETWORK=$NET"
  echo 'EXPECTED_F2P_NODES=3; EXPECTED_P2P_NODES=103; EXPECTED_INVOCATIONS=318'
  echo 'CONTROL_EDIT=TOKEN_CREATION_AND_RELATIVE_APP_URL; TEST_INFORMED_NOT_MODEL_GENERATION; A5_R1=STOP'
} > "$OUT/EXECUTION_METADATA.txt"
PASS=$(od -An -N24 -tx1 /dev/urandom | tr -d ' \n')
printf 'POSTGRES_USER=postgres\nPOSTGRES_PASSWORD=%s\nPOSTGRES_DB=%s\n' "$PASS" "$DB" > "$ROOT/db.env"
{
 printf 'DATABASE_URL=postgresql://postgres:%s@wp2-opws-pg-smoke:5432/%s\n' "$PASS" "$DB"
 printf 'POSTGRES_URL=postgresql://postgres:%s@wp2-opws-pg-smoke:5432/%s\n' "$PASS" "$DB"
 printf 'POSTGRES_HOST=wp2-opws-pg-smoke\nPOSTGRES_DB=%s\nPOSTGRES_USER=postgres\nPOSTGRES_PASSWORD=%s\nPOSTGRES_PORT=5432\n' "$DB" "$PASS"
 printf 'PGHOST=wp2-opws-pg-smoke\nPGDATABASE=%s\nPGPORT=5432\nPGUSER=postgres\nPGPASSWORD=%s\n' "$DB" "$PASS"
 printf 'DJANGO_SETTINGS_MODULE=saleor.tests.settings\nUV_OFFLINE=1\nUV_CACHE_DIR=/opt/hydrated_uv_cache\nUV_NO_CONFIG=1\nUV_NO_MANAGED_PYTHON=1\nUV_LINK_MODE=copy\nPYTHONDONTWRITEBYTECODE=1\n'
} > "$ROOT/eval.env"
chmod 600 "$ROOT/db.env" "$ROOT/eval.env";unset PASS
# No external network inside measurement. New isolated DB/network are destroyed at exit.
docker network create --internal --driver bridge --label track1_1_d3_control=1 "$NET" >/dev/null;NETWORK_CREATED=1
[[ "$(docker network inspect "$NET" --format '{{.Internal}}')" == true ]] || { echo STOP_NETWORK_NOT_INTERNAL;exit 15; }
docker run -d --pull never --name "$PG" --network "$NET" --network-alias wp2-opws-pg-smoke \
 --env-file "$ROOT/db.env" --security-opt no-new-privileges --memory 3g --pids-limit 512 postgres:15-alpine >/dev/null
PG_CREATED=1
READY=0;for i in $(seq 1 45);do if docker exec "$PG" pg_isready -U postgres -d "$DB" >/dev/null 2>&1;then READY=1;break;fi;sleep 2;done
[[ "$READY" == 1 ]] || { echo STOP_DB_UNAVAILABLE;exit 16; }
[[ -z "$(docker port "$PG" 2>/dev/null)" ]] || { echo STOP_PG_HOST_PORT;exit 17; }
echo 'DOCKER_ISOLATED_DB_NETWORK=PASS' | tee -a "$OUT/EXECUTION_METADATA.txt"
cat > "$ROOT/evaluate.sh" <<'INNER'
#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
cd /workspace/wt_t
python - <<'PY_EGRESS'
import socket
for addr in [('1.1.1.1',443),('8.8.8.8',53)]:
 sock=socket.socket();sock.settimeout(3)
 try:sock.connect(addr)
 except OSError:print('EXTERNAL_EGRESS_BLOCKED',addr,flush=True)
 else:raise SystemExit('STOP_EXTERNAL_EGRESS_ALLOWED:'+str(addr))
 finally:sock.close()
with socket.create_connection(('wp2-opws-pg-smoke',5432),timeout=10):
 print('DEDICATED_POSTGRES_TCP_PASS',flush=True)
PY_EGRESS
python --version
uv --version
uv venv /opt/venv > /results/venv.log 2>&1 || { echo STOP_VENV;cat /results/venv.log;exit 31; }
# Exact archived-wheel hashes from frozen uv.lock; cache was hydrated outside measurement.
# UV_OFFLINE=1 plus the physical internal Docker bridge are two independent no-egress controls.
[[ "${UV_OFFLINE:-}" == 1 ]] || { echo STOP_UV_OFFLINE_NOT_SET;exit 32; }
echo 'LOCK_HASHED_OFFLINE_INSTALL_START'
uv pip install --offline --require-hashes \
  -r /inputs/FROZEN_DEV_HASHED.txt --python /opt/venv/bin/python \
  > /results/install.log 2>&1 || { echo STOP_HASHED_OFFLINE_INSTALL;tail -50 /results/install.log;exit 33; }
uv pip check --python /opt/venv/bin/python > /results/installed_check.log 2>&1 || { echo STOP_INSTALLED_CHECK;cat /results/installed_check.log;exit 34; }
[[ "$(sha256sum /workspace/wt_t/uv.lock | cut -d' ' -f1)" == 'a4c21a2deb52e20e52b691857fd5adae8f130e6844626c18b3aaebc688eb2d66' ]] || { echo STOP_UV_LOCK_DRIFT;exit 35; }
echo 'HASHED_OFFLINE_DEPENDENCIES=PASS'
/opt/venv/bin/python -m pytest --version
/opt/venv/bin/python - <<'PY'
import django
from django.conf import settings
django.setup()
from django.db import connection
engine=connection.settings_dict.get('ENGINE','')
host=connection.settings_dict.get('HOST','')
if 'postgresql' not in engine or host!='wp2-opws-pg-smoke':
 raise SystemExit('STOP_DB_SETTINGS_NOT_DEDICATED_POSTGRES:'+engine+':'+host)
connection.ensure_connection()
print('DJANGO_FRESH_DB_CONNECTION=PASS')
connection.close()
PY
# Static code quality is a separate gate, not a substitute for behavioral E2E.
/opt/venv/bin/ruff check saleor/app/installation_utils.py saleor/app/manifest_validations.py > /results/D3_RUFF_CHECK.log 2>&1 || { echo STOP_D3_RUFF; cat /results/D3_RUFF_CHECK.log;exit 36; }
if /opt/venv/bin/ruff format --check saleor/app/installation_utils.py saleor/app/manifest_validations.py > /results/D3_RUFF_FORMAT.log 2>&1; then
  echo 'D3_RUFF_FORMAT=PASS'
else
  echo 'D3_RUFF_FORMAT=NOT_QUALIFIED_REVIEW_REPORT; F2P_GATE_STILL_REQUIRED'
fi
echo 'D3_RUFF_LINT=PASS'
# Independent 3x physical pytest processes, no semantic rescue and no test modifications.
/opt/venv/bin/python /evaluator/T11_RUN_TEST_NODES_IN_CONTAINER.py --stage F2P \
 --results /results/F2P --worktree /workspace/wt_t \
 --expected-source-sha /expected.json
echo 'F2P_9_PHYSICAL_INVOCATIONS=COMPLETED'
# Validate JUnit identity and hashes before P2P (assertion failures remain genuine results).
/opt/venv/bin/python - <<'PY'
import json,pathlib,hashlib,xml.etree.ElementTree as ET
r=pathlib.Path('/results/F2P');lines=(r/'COMMAND_LEDGER.jsonl').read_text().splitlines()
if len(lines)!=9:raise SystemExit('STOP_F2P_LEDGER_NOT_9')
for x in lines:
 e=json.loads(x);p=r/f"r{e['repetition']}_f{e['index']}.xml"
 if e['return_code'] not in (0,1) or not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=e['xml_sha256']:
  raise SystemExit('STOP_F2P_JUNIT_OR_RC')
 cases=ET.parse(p).findall('.//testcase')
 if len(cases)!=1:raise SystemExit('STOP_F2P_JUNIT_NODE_COUNT')
print('F2P_9_JUNIT_INTEGRITY=PASS')
PY
/opt/venv/bin/python /evaluator/T11_D3_F2P_GATE.py --results /results/F2P --out /results/D3_F2P_GATE.json || { echo 'D3_F2P_FUNCTIONAL_STOP; P2P_NOT_RUN';exit 61; }
echo 'D3_F2P_STABLE_3_OF_3=PASS; STARTING_P2P'
/opt/venv/bin/python /evaluator/T11_RUN_TEST_NODES_IN_CONTAINER.py --stage P2P \
 --results /results/P2P --worktree /workspace/wt_t \
 --expected-source-sha /expected.json
echo 'P2P_309_PHYSICAL_INVOCATIONS=COMPLETED'
INNER
chmod 700 "$ROOT/evaluate.sh"
set +e
( docker run --rm --pull never --name "t11-d3-eval-${TAG//_/-}" \
  --network "$NET" --env-file "$ROOT/eval.env" --cap-drop ALL \
  --security-opt no-new-privileges --pids-limit 1024 --memory 8g --cpus 6 \
  --mount "type=bind,src=$ROOT/wt_t,dst=/workspace/wt_t" \
  --mount "type=bind,src=$KIT,dst=/evaluator,readonly" \
  --mount "type=bind,src=$ROOT/expected.json,dst=/expected.json,readonly" \
  --mount "type=bind,src=$ROOT/evaluate.sh,dst=/runner_entry.sh,readonly" \
  --mount "type=bind,src=$PREP/FROZEN_DEV_HASHED.txt,dst=/inputs/FROZEN_DEV_HASHED.txt,readonly" \
  --mount "type=bind,src=$CACHE,dst=/opt/hydrated_uv_cache" \
  --mount "type=bind,src=$OUT,dst=/results" \
  --entrypoint /bin/bash "$IMAGE" /runner_entry.sh ) 2>&1 | tee "$OUT/CONTAINER_STDOUT_STDERR.log"
TEST_RC=${PIPESTATUS[0]};set -e
[[ "$TEST_RC" == 0 ]] || { echo "STOP_D3_TEST_OR_INFRA_RC=$TEST_RC";tail -30 "$OUT/CONTAINER_STDOUT_STDERR.log";exit 40; }
EQ "$ROOT/wt_t/$T1" "$D3S1";EQ "$ROOT/wt_t/$T2" "$D3S2"
EQ "$STAGE/$T1" "$S1";EQ "$STAGE/$T2" "$S2"
python3 "$KIT/T11_D3_AUDIT_106.py" --results "$OUT" --out "$OUT/D3_JUNIT_AUDIT.json" --repair-receipt "$OUT/D3_STAGE/D3_REPAIR_RECEIPT.json" | tee "$OUT/AUDITOR.log"
AUDIT_RC=${PIPESTATUS[0]}
[[ "$AUDIT_RC" == 0 ]] || { echo "STOP_AUDITOR_RC=$AUDIT_RC";exit 41; }
python3 - "$OUT/D3_JUNIT_AUDIT.json" <<'PY_FINAL'
import json,sys
j=json.load(open(sys.argv[1]))
assert j['junit_integrity_status']=='COMPLETE' and j['physical_invocations_verified']==318
assert j['f2p_distinct_stable_pass']==3 and j['p2p_distinct_stable_pass']==103, 'D3_FUNCTIONAL_QUALITY_GATE_FAIL'
print(f"D3_F2P_STABLE_PASS={j['f2p_distinct_stable_pass']}/3")
print(f"D3_P2P_STABLE_PASS={j['p2p_distinct_stable_pass']}/103")
print('ORIGINAL_A5_R1=STOP; D3_TEST_INFORMED_REPAIR_CONTROL=YES; NOT_MODEL_GENERATION')
PY_FINAL
python3 "$KIT/T11_D3_QUALITY_REPORT.py" --results "$OUT" --out "$OUT/D3_QUALITY_REPORT.json"
echo 'D3_106_HASHED_OFFLINE_E2E=COMPLETE_TEST_INFORMED_REPAIR_CONTROL' | tee -a "$OUT/EXECUTION_METADATA.txt"
echo "EVIDENCE_DIR=$OUT"
