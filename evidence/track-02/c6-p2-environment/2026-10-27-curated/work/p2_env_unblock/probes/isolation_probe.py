# -*- coding: utf-8 -*-
"""T5 NON-CANDIDATE isolation & limits probes (run inside r3, --network none)."""
import json, socket, os, sys, threading, time
res = {}

# 1) outbound network MUST fail (no default route / no interfaces beyond lo)
try:
    s = socket.create_connection(("8.8.8.8", 53), timeout=5)
    res["outbound_tcp"] = "UNEXPECTED_OK"
    s.close()
except OSError as e:
    res["outbound_tcp"] = f"BLOCKED({type(e).__name__})"

# 2) interfaces
outs = os.popen("cat /proc/net/fib_trie 2>/dev/null || ip addr 2>/dev/null || true").read()
res["has_external_interface_hint"] = ("eth0" not in outs and "ens" not in outs)

# 3) read-only rootfs: cannot write /tmp or / (only /scratch, /scratch-dir writable)
try:
    open("/tmp/c6_probe_write.txt", "w").write("x")
    res["rootfs_readonly"] = "NOT_ENFORCED"
except OSError as e:
    res["rootfs_readonly"] = f"ENFORCED({getattr(e,'errno',None)})"
try:
    with open("/scratch-dir/probe_w.txt", "w") as f:
        f.write("ok")
    res["scratch_dir_writable"] = True
except OSError as e:
    res["scratch_dir_writable"] = f"FAIL({e})"
try:
    with open("/scratch/probe_w.txt", "w") as f:
        f.write("ok")
    res["scratch_tmpfs_writable"] = True
except OSError as e:
    res["scratch_tmpfs_writable"] = f"FAIL({e})"

# 4) memory cap probe is done via container flags (rc 137) — see bash wrapper.
print(json.dumps(res, indent=1, sort_keys=True))