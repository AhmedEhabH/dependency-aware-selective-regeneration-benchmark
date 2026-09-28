PHASE_REPORT — G1/G2/G3 (Authority + Governance + Reconciliation)
Mission: MISSION-12B V2.1 AUTONOMOUS_UNATTENDED
Timestamp: 2026-09-28 (UTC)

G1 PASS
- G1.1 Mission-11 authority file present and read.
- G1.2 Byte-for-byte copy to _workspace/active/M12B_AUTHORITY_ARCHIVE/; SHA256 match.
  SRC==DST==0DCBA2C5...A737DC2 (67,330 bytes).
- G1.3 C22 (line 227) and D63 (line 203) extracted verbatim to
  v21/governance/mission11_rule_extracts.json.
- G1.4 D63 vs TRANSPORT_V21 comparison recorded as intentional prospective
  amendment (v21/governance/d63_v21_comparison.json). v21 policy unchanged.

G2 PASS
- history_and_deviations.json + docs/MISSION12B_V21_GOVERNANCE_2026-09-28.md written.
- Records: v1 instrument invalid, Mission-12 C22 max-attempt breach, v2 J/K/L
  diagnostic-only, v2 paid partial run (10 eps / 11 ledger / $0.025718400 /
  64,608 / 6,384), post-freeze driver changes, v2 HOLD, snapshot SHA
  f89ccd54..., prospective OPTION A reset, no v2 evidence reuse.
- CHECK: no v1/v2 evidence bytes changed (verified via git status/diff).

G3 PASS
- v21/governance/provenance_reconciliation.json written.
- G3.1 Scope semantic hashes: GOLD/RMCSS/AGENT/PLACEBO all match v1 freeze.
- G3.2 Harness V3 identity resolved (non-null): version wp2-harness-v3-2026-09-26,
  spec_sha256 e7897ba0..., git_head 9216c299...; v2 null spec_sha256 flagged.
- G3.3 AGENT scope helper bug documented (build_arm_scopes reads d.get(task_id)
  but data is under 'per_task'); generator-equivalent loader identified.

NEXT: T0 create v21 namespace + HOLD + design_v21.json.
