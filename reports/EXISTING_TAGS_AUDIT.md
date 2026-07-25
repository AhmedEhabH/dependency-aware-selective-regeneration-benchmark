# Existing Tags Audit

**Date:** 2026-07-25
**Branch:** audit/arm-to-protocol-execution
**Current HEAD:** 0c831e397faa15ae31dc1442c5273f1e8d134253 (main)

---

## Tag Analysis Summary

| Tag | Peeled Commit | Date | Declared Meaning | Actual State | Accurate? | Recommendation |
|-----|---------------|------|------------------|--------------|-----------|----------------|
| v0.5.0-rc.1 | 1e795bd8cbdbb95d09f335affc39d68a5b1cedd1 | 2026-07-22 05:51:19 +0300 | Phase 4D execution core complete, Phase 4E/4F split documented | Merge commit for docs/plan merge | Yes | **Keep** |
| v0.6.0-rc.1 | 76b328f3324076ebdb37e95f0bb12aff868bef50 | 2026-07-23 01:14:11 +0300 | Kaggle smoke candidate. Local engineering validation complete. Real Qwen smoke pending. No pilot/confirmatory results. | Pre-smoke code with mypy fixes, profile alignment, readiness report | Yes | **Keep** |
| v0.7.0-smoke-passed | 0c582504a8a5b9a36503bbe2e092768b46855bd5 | 2026-07-23 05:31:24 +0300 | Kaggle real smoke passed. 7/7 arms executed. Real Qwen inference confirmed. Non-publication evidence. Pilot/research not started. | Post-smoke merge; orchestration smoke passed but **4/7 arms mismatched vs protocol** (llm_by_design=True but llm_attached=False) | **Partially** — orchestration passed, arms not protocol-compliant | **Deprecate** |

---

## Detailed Tag Reports

### v0.5.0-rc.1

**Tag object:** Annotated tag
**Peeled commit:** `1e795bd8cbdbb95d09f335affc39d68a5b1cedd1`
**Date:** 2026-07-22 05:51:19 +0300
**Tagger:** AhmedEhabH <ahmed.ehab.h@gmail.com>

**Tag message:**
```
v0.5.0-rc.1 — Phase 4D execution core complete, Phase 4E/4F split documented
```

**Commit message:**
```
docs(plan): merge Phase 4E/4F split documentation
```

**Analysis:**
- Merge commit combining documentation for Phase 4E/4F split
- Represents a documentation milestone, not a scientific execution milestone
- Accurately describes the repository state at that commit
- No scientific claims about benchmark execution

**Recommendation:** **Keep** — valid historical marker for Phase 4D documentation completion.

---

### v0.6.0-rc.1

**Tag object:** Annotated tag
**Peeled commit:** `76b328f3324076ebdb37e95f0bb12aff868bef50`
**Date:** 2026-07-23 01:14:11 +0300
**Tagger:** AhmedEhabH <ahmed.ehab.h@gmail.com>

**Tag message:**
```
Kaggle smoke candidate.
Local engineering validation complete.
Real Qwen smoke execution pending.
No pilot or confirmatory results included.
```

**Commit message:**
```
feat: release-readiness check — mypy fixes, protocol-aligned profiles, notebook safety, readiness report
- Fix 5 mypy strict errors (imports from enums directly, tuple type args)
- Replace PROFILE_SCENARIO_COUNTS with typed ExecutionProfile dataclasses
- Align pilot profile: 12 scenarios x 2 strategies x 2 reps
- Align research profile: 24 scenarios x 4 full-evolution strategies x 3 reps
- Add IMPACT_ONLY_STRATEGIES to skip unnecessary full generation
- Update smoke/pilot/research YAML configs with labels and is_publication
- Clear notebook outputs; enforce smoke as default; document explicit profile selection
- Verify local_files_only=True in KaggleQwenBackend
- Add meta tags to output JSON for publication/non-publication marking
- Produce reports/KAGGLE_SMOKE_READINESS_REPORT.md
```

**Analysis:**
- Represents "code ready for Kaggle smoke" state
- Profile definitions align with FINAL_RESEARCH_PROTOCOL.md
- IMPACT_ONLY_STRATEGIES flag added but not yet implemented in execution
- KAGGLE_SMOKE_READINESS_REPORT.md produced
- No actual Kaggle execution yet

**Recommendation:** **Keep** — valid pre-smoke readiness marker.

---

### v0.7.0-smoke-passed

**Tag object:** Annotated tag
**Peeled commit:** `0c582504a8a5b9a36503bbe2e092768b46855bd5`
**Date:** 2026-07-23 05:31:24 +0300
**Tagger:** AhmedEhabH <ahmed.ehab.h@gmail.com>

**Tag message:**
```
Kaggle real smoke passed.

Seven of seven strategy arms executed successfully.
Real Qwen2.5-Coder inference confirmed.
Smoke results are non-publication engineering evidence.
Pilot and research experiments have not started.
```

**Commit message:**
```
merge: fix/kaggle-graph-strategy-wiring into main
```

**Analysis:**
- Merge of `fix/kaggle-graph-strategy-wiring` branch
- Orchestration smoke test passed: 7/7 arms ran without error on Kaggle
- Real Qwen inference confirmed for `agent` arm
- **However:** The arm-to-protocol audit reveals that at this commit:
  - 4/7 arms have `llm_by_design=True` but `llm_attached=False` (monolithic, selective, delta_mcp, code_plan)
  - Only `agent` arm actually uses an LLM backend
  - The "smoke passed" refers to **orchestration validity** (no crashes, checkpoint/resume works, HF sync works)
  - It does **not** mean the arms are scientifically protocol-compliant
  - The tag name "smoke-passed" implies scientific smoke validation; actual state is orchestration-only

**Recommendation:** **Deprecate** — tag name suggests protocol-compliant smoke; audit shows 4 mismatched arms. Do not use as evidence that scientific arms are validated. If kept, must be annotated with disclaimer.

---

## Commit History Context

```
v0.5.0-rc.1 (1e795bd) → v0.6.0-rc.1 (76b328f) → v0.7.0-smoke-passed (0c58250) → ... → HEAD (0c831e3)
```

**Current HEAD (0c831e3)** is 8 commits ahead of v0.7.0-smoke-passed:
- SU-0008 cross-session reporting rebuild
- SU-0007 post-validation fixes
- SU-0006 recovery activation path
- SU-0005 explicit resume identity
- SU-0004 HF candidate rejection diagnosis
- SU-0003 HF auto-resume discovery
- SU-0002 runs dir NameError fix
- Canonical project remediation

---

## Verification Commands

```bash
# Peeled commits
git rev-list -n 1 v0.5.0-rc.1   # 1e795bd8cbdbb95d09f335affc39d68a5b1cedd1
git rev-list -n 1 v0.6.0-rc.1   # 76b328f3324076ebdb37e95f0bb12aff868bef50
git rev-list -n 1 v0.7.0-smoke-passed  # 0c582504a8a5b9a36503bbe2e092768b46855bd5

# Tag objects
git show v0.5.0-rc.1 --no-patch
git show v0.6.0-rc.1 --no-patch
git show v0.7.0-smoke-passed --no-patch

# Full history
git log --oneline --decorate --graph --all
```

---

## Tag Object vs Peeled Commit

All three tags are **annotated tags** (tag objects pointing to commits). The `git show` output shows tag metadata; `git rev-list -n 1 <tag>` returns the peeled commit hash.

| Tag | Tag Object Exists | Peeled Commit | Verified |
|-----|-------------------|---------------|----------|
| v0.5.0-rc.1 | Yes | 1e795bd8cbdbb95d09f335affc39d68a5b1cedd1 | ✓ |
| v0.6.0-rc.1 | Yes | 76b328f3324076ebdb37e95f0bb12aff868bef50 | ✓ |
| v0.7.0-smoke-passed | Yes | 0c582504a8a5b9a36503bbe2e092768b46855bd5 | ✓ |

---

## Impact on Audit Branch

This audit branch (`audit/arm-to-protocol-execution`) is created from HEAD (0c831e3), which is **post** v0.7.0-smoke-passed. The tag audit confirms that the "smoke-passed" tag was applied to a state with known (but undocumented) arm mismatches. This audit documents those mismatches for researcher decision.

**No new tags should be created** until arm mismatches are resolved and a genuine protocol-compliant smoke is executed.

---

## Recommendation Summary

| Tag | Keep / Deprecate / Do-Not-Use |
|-----|-------------------------------|
| v0.5.0-rc.1 | **Keep** |
| v0.6.0-rc.1 | **Keep** |
| v0.7.0-smoke-passed | **Deprecate** — add disclaimer: "orchestration-smoke-only; 4/7 arms mismatched vs protocol design" |

---
*End of Tag Audit*