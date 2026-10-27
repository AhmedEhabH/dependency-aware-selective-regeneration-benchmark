# TRACK02 C6 P2 — r3: layered fix on r2 (before-after install ordering)
# r2 installed 237 era packages but `before-after==1.0.1` failed once in the
# phaseA loop because its `mock` dependency had not yet been installed (mock is
# built later in phaseB). mock is present in r2; this layer installs
# before-after exactly (local pre-built wheel, --no-deps) and refreshes the
# frozen pip-freeze ledger.
FROM envcanon/saleor-c6-p2-py39-era:r2
RUN pip install --no-index --no-cache-dir --find-links=/offwh --timeout 60 --retries 0 \
        --no-deps --no-build-isolation /offwh/before_after-1.0.1-py3-none-any.whl -q \
 && pip freeze > /etc/c6-pip-freeze.txt \
 && python - <<'PY'
import json, pkg_resources
d=json.load(open("/etc/c6-provenance.json"))
d["r3"]={"parent":"envcanon/saleor-c6-p2-py39-era:r2",
         "fix":"before-after==1.0.1 installed from local prebuilt wheel (mock ordering)"}
d["before_after_version"]=pkg_resources.get_distribution("before-after").version
json.dump(d, open("/etc/c6-provenance.json","w"), indent=2)
PY
LABEL org.c6.r3.fix="before-after install ordering"