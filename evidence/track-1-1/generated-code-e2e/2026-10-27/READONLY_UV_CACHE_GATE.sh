#!/usr/bin/env bash
# Evaluator-only, read-only uv cache qualification: no Docker, no pytest, no network.
set -Eeuo pipefail
D='/opt/wp2_v2/m17-env/uv-cache'
DIST="$D/archive-v0/78t-8_kYua-4CL9A/amqp-5.3.1.dist-info"
PKG="$D/archive-v0/78t-8_kYua-4CL9A/amqp"
IDX="$D/wheels-v6/pypi/amqp"
for x in "$DIST/METADATA" "$DIST/RECORD" "$PKG/__init__.py"; do
  test -f "$x" || { echo "STOP_EXPECTED_CACHE_FILE_MISSING:$x"; exit 10; }
done
test -d "$IDX" || { echo 'STOP_WHEELS_V6_INDEX_MISSING'; exit 11; }
python3 - "$DIST/METADATA" <<'PY_META'
from pathlib import Path
import email,sys
meta=email.message_from_bytes(Path(sys.argv[1]).read_bytes())
name=meta.get('Name','').strip().lower().replace('_','-')
version=meta.get('Version','').strip()
if (name,version)!=('amqp','5.3.1'):
 raise SystemExit(f'STOP_CACHE_DIST_METADATA_MISMATCH:{name}:{version}')
print('AMQP_CACHE_METADATA_NAME_VERSION=PASS')
PY_META
printf 'AMQP_CACHE_METADATA_SHA256='; sha256sum "$DIST/METADATA" | cut -d' ' -f1
printf 'AMQP_CACHE_RECORD_SHA256='; sha256sum "$DIST/RECORD" | cut -d' ' -f1
printf 'WHEELS_V6_AMQP_ENTRIES='; find "$IDX" -maxdepth 2 -type f | wc -l
printf 'UV_CACHE_DISK_KIB='; du -sk "$D" | cut -f1
printf 'UV_CACHE_DISK_AVAILABLE_KIB='; df -Pk /opt | awk 'NR==2{print $4}'
echo 'AMQP_5_3_1_CACHE_METADATA=PASS'
echo 'UV_CACHE_FULL_OFFLINE_CLOSURE=NOT_YET_QUALIFIED'
echo 'MODEL_CALLS=0; PYTEST=NOT_RUN; DOCKER_MUTATIONS=0'
