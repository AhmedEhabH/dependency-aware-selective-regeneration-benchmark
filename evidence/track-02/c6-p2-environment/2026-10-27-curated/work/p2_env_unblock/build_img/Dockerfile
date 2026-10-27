# TRACK02 C6 P2 — historical environment (OFFLINE, reproducible)
# Mission TRACK02-C6-P2-ENV-UNBLOCK (2026-10-27)
#
# Base : envcanon/saleor-env-r4b-py39-native (local tag; on-disk ID verified
#        separately: sha256:3220486db0d8f7649b29bfe01875a1ef794c860539e2713587d9d32f5bd91b89)
#        Debian 12 bookworm, CPython 3.9.25, pip 23.0.1
# P    : 5b0e5206c5fd30d81438b6489d0441df51038a85  (runtime.txt = python-3.9.14)
# T    : 06d25ce29c984d9af0f8759044cd80aa8a835e83
#
# Bake set = requirements_dev.txt@P (245 pins) minus win32-only python-magic
# bin, plus promise==2.3. Phase A = 221 entries with local wheels (incl. local
# pre-built psycopg2==2.9.4 cp39 and before-after==1.0.1); Phase B = 23
# sdist-only entries installed best-effort (pure-python; failures are RECORDED
# at /etc/c6/install_failures.txt, never silently dropped).
# NO network: pip --no-index against the hash-pinned subset offwh/.

FROM envcanon/saleor-env-r4b-py39-native:latest

COPY offwh /offwh
COPY phaseA.txt phaseB.txt /tmp/

RUN set -eu && \
    pip install --no-index --no-cache-dir --find-links=/offwh --timeout 60 --retries 0 \
        --no-deps --no-build-isolation "setuptools==65.5.0" "setuptools-scm==10.3.4" "vcs_versioning==2.6.0" -q && \
    mkdir -p /etc/c6 && : > /etc/c6/phaseA_failures.txt && \
    while IFS= read -r pkg; do \
        [ -z "${pkg}" ] && continue; \
        pip install --no-index --no-cache-dir --find-links=/offwh --timeout 60 --retries 0 \
            --no-build-isolation "${pkg}" -q \
        || echo "A|${pkg}" >> /etc/c6/phaseA_failures.txt; \
    done < /tmp/phaseA.txt && \
    : > /etc/c6/phaseB_failures.txt && \
    while IFS= read -r pkg; do \
        [ -z "${pkg}" ] && continue; \
        pip install --no-index --no-cache-dir --find-links=/offwh --timeout 60 --retries 0 \
            --no-build-isolation "${pkg}" -q \
        || SETUPTOOLS_SCM_PRETEND_VERSION="${pkg#*==}" pip install --no-index --no-cache-dir \
            --find-links=/offwh --timeout 60 --retries 0 --no-use-pep517 "${pkg}" -q \
        || echo "B|${pkg}" >> /etc/c6/phaseB_failures.txt; \
    done < /tmp/phaseB.txt && \
    pip freeze > /etc/c6-pip-freeze.txt && \
    python -c "import json;json.dump({'mission':'TRACK02-C6-P2-ENV-UNBLOCK','base':'envcanon/saleor-env-r4b-py39-native','base_sha256':'3220486db0d8f7649b29bfe01875a1ef794c860539e2713587d9d32f5bd91b89','p':'5b0e5206c5fd30d81438b6489d0441df51038a85','t':'06d25ce29c984d9af0f8759044cd80aa8a835e83','runtime_txt':'python-3.9.14','interpreter_baked':'3.9.25','offline':True,'network':0,'excluded_lint_tooling':['pylint','pylint-celery','pylint-django','pylint-plugin-utils'],'excluded_win32_only':['python-magic-bin']},open('/etc/c6-provenance.json','w'),indent=2)"

LABEL org.c6.mission="TRACK02-C6-P2-ENV-UNBLOCK" \
      org.c6.base_sha256="3220486db0d8f7649b29bfe01875a1ef794c860539e2713587d9d32f5bd91b89" \
      org.c6.offline="true" \
      org.c6.p="5b0e5206c5fd30d81438b6489d0441df51038a85" \
      org.c6.t="06d25ce29c984d9af0f8759044cd80aa8a835e83"

WORKDIR /opt/saleor
ENV C6_IMAGE_ROLE=p2-derived-pinned PIP_DISABLE_PIP_VERSION_CHECK=1