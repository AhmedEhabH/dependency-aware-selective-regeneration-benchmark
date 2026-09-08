#!/usr/bin/env python3
"""Run validation gates and audit."""
import sys
sys.path.insert(0, '.')

from src.benchmark.external_validity.validate_gates import run_all_gates, independent_audit

if __name__ == "__main__":
    gates_ok = run_all_gates()
    if gates_ok:
        audit_ok = independent_audit()
        sys.exit(0 if audit_ok else 1)
    else:
        sys.exit(1)