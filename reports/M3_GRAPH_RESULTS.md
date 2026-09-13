# M3 Graph Results — C0 / C1 / C2

**Study ID:** `scientific-djangocms-graph-c0-c1-c2-01`
**Classification:** POST-HOC EXPLORATORY DEVELOPMENT-SET GRAPH ABLATION
**Date:** 2026-09-13
**Model / provider:** Qwen3-Coder-480B-A35B-Instruct @ OpenRouter/DeepInfra
(`deepinfra/turbo`, fp4), temperature 0, completion cap 16384 (non-binding),
Graph study over the frozen 144-path djangoCMS 5.0.0 universe.
**Branch:** `research/graph-c0-c1-c2-01`
**Zero-API verifier:** `scripts/verify_graph_ablation_claims.py` (**40/40 PASS**)

---

## 1. Design recap

| Condition | Graph role | Cells | New calls |
|---|---|---|---|
| C0 | Graph OFF (Sparse-v2) | 30 (REUSED audited M1B Sparse-v2, byte-identical prompts) | 0 |
| C1 | Graph Hints (full 562-edge AST graph, soft evidence) | 30 | 30 |
| C2 1-hop | Graph-Gated Disclosure (risk zone = 1-hop of seeds; mandatory explicit decision in-zone) | 30 | 30 |
| C2 2-hop | Graph-Gated Disclosure (risk zone = 2-hop) | 30 | 30 |

- **C2 3-hop was NOT run**: the pre-registered eligibility rule
  (|zone3| ≤ 115 AND |zone3| > |zone2| for all scenarios) failed — 3-hop zones
  are 129–130 of 144 (~90%, effectively repository-wide). Frozen before any
  call; no post-hoc tuning.
- Seed sets (frozen algorithm v1, inference-time-only, no gold): 2–5 seeds
  per scenario. Risk zones: 1-hop 25–41, 2-hop 111–119.
- New scientific cells: **90** (all executed, all persisted with raw response
  + SHA-256; 90/90 sidecars verified). Hard cost ceiling $2.00.

## 2. Headline results

| Condition | Valid/30 | Failed | P | R | F1 | FNR | FN | FP | mean comp tok | mean prompt tok | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **C0** (M1B reuse) | 30 | 0 | 0.7211 | **0.8833** | 0.7940 | 0.1167 | **14** | 41 | 809 | 2,640 | 0.0480 |
| **C1** (Graph Hints) | 30 | 0 | **0.8136** | 0.8000 | **0.8067** | 0.2000 | 24 | **22** | 855 | 8,052 | 0.0981 |
| **C2 1-hop** (Gated) | **2** | 28 | 0.2727 | 0.6000 | 0.3750 | 0.4000 | 4 | 16 | 1,365 | 3,262 | 0.0703 |
| **C2 2-hop** (Gated) | **0** | 30 | — | — | — | — | — | — | 860 | 4,493 | 0.0662 |

Study totals (new cells): 90 recorded, **32 valid / 58 failed**, 0 truncations,
0 transport failures; 474,210 prompt + 92,413 completion = 566,623 total
tokens; recorded API cost **$0.234673** (< $2.00 ceiling).

## 3. C0 → C1 (Graph Hints vs Graph OFF)

| Metric | Δ (C1 − C0) | Direction |
|---|---|---|
| ΔPrecision | **+0.0925** | improves |
| ΔRecall | **−0.0833** | degrades |
| ΔF1 | **+0.0127** | marginal |
| ΔFN | **+10** (14 → 24) | **degrades (opposite of the primary hypothesis)** |
| ΔFP | **−19** (41 → 22) | improves |
| Δmean total tokens | **+5,458** (≈ +207%: graph block inflates prompts) | degrades |
| Δcost | **+$0.0501** (30 cells) | degrades |

**Reading.** Graph Hints made the model markedly more conservative and more
precise: FP fell by nearly half and precision rose +9.2pp, lifting F1
marginally. But recall FELL 8.3pp and FN rose from 14 to 24 — the exact
metric M3 was designed to reduce. Soft evidence therefore steered the model
toward fewer, more confident selections, trading recall for precision. The
**graph-hint signal is MIXED**: it improves precision/F1 in 3/6 scenarios,
hurts recall in 2, and moves the FN objective in the WRONG direction
overall. S006 improves (see §5); S007 degrades sharply (§6).

## 4. C0 → C2 (Graph-Gated Disclosure)

| Metric | C2 1-hop (valid n=2) | C2 2-hop (valid n=0) |
|---|---|---|
| Mandatory-zone disclosure compliance | **2/30 (6.7%)** | **0/30 (0%)** |
| Failed cells | 28 (all mandatory-disclosure-failure) | 30 (all mandatory-disclosure-failure) |
| In-zone ids omitted per failed run | median 21.5 (of 25–41 zone ids) | all 30 runs non-compliant |

**Reading.** The mandatory-disclosure mechanism as designed is **operationally
infeasible for this model under the sparse schema**: the model's natural
sparse output length (~5–20 decisions) is far below the in-zone mandate
(25–41 ids at 1-hop; 111–119 at 2-hop), so it omits most in-zone candidates
and the cells fail closed. Because 2-hop zones cover 78–83% of the universe,
C2 2-hop effectively demanded near-full explicit serialization under a
policy that forbids PRESERVE rows — a design tension the protocol froze and
the study exposed. The two surviving C2 1-hop runs both happened to be S006
(recall 1.0 on one run), but n=2 is not a semantic comparison basis. The
honest C2 finding is a **feasibility result: mandatory disclosure compliance
collapsed (6.7% → 0%) as zone size grew**.

## 5. S006 deep diagnosis

- **C0 (Sparse-v2)**: R 0.333 / F1 0.278 / FN 10 — Sparse-v2 misses
  `cms/utils/plugins.py` (4/5 reps) and `cms/admin/placeholderadmin.py`
  (5/5). Both are **graph neighbors of the seed `cms/models/pluginmodel.py`
  (distance 1)**, i.e. inside the 1-hop risk zone.
- **C1 (Graph Hints)**: R 0.400 / F1 **0.414** / FN 9 — improved, but the
  improvement is NOT from recovering the structural neighbors: it still
  misses `placeholderadmin.py` (5/5) and `plugins.py` (4/5). The F1 gain
  comes from lower FP (16 → 8) via more conservative selection.
- **C2 1-hop**: the ONLY 2 valid runs of the whole C2 arm were S006 (1 valid,
  1 of the S006 runs). On the single valid S006 C2-1hop run: R 1.0, FN 0 —
  the mandated disclosure forced decisions on the missed neighbors and
  recovered both gold files. This is the single positive instance of the
  disclosure mechanism, but n=1.
- **Why S006 partially improves in C1**: the model sees the explicit
  import edges (`pluginmodel -> plugins`, `pluginmodel -> placeholderadmin`)
  and selects fewer non-gold files, but the soft evidence alone does not
  reliably flip the model's decision on the utility module (`plugins.py`)
  that consumes the changed model. Only a HARD mandate (C2) forced it — and
  only in the single run where the model complied.

## 6. Which scenario gets worse and why

- **S007 degrades the most (C1)**: recall 0.886 → 0.686 (FN 4 → 11). S007 is
  the cross-cutting scenario (7 gold files spanning models/admin/api/signals/
  toolbar/permissions). With graph hints the model became over-conservative
  and dropped three gold files — two of them (`cms/api.py`,
  `cms/models/permissionmodels.py`) at distance 2 from the seeds (outside the
  1-hop zone) and `cms/utils/page_permissions.py` (distance 1). The hints
  made the model treat the graph as a scope boundary rather than a cue to
  broaden, punishing the widest-scope scenario.
- **S002/S005 degrade mildly (C1)**: S002 F1 0.909 → 0.714 (FP 1 → 4);
  S005 recall 1.0 → 0.84 (misses `cms/admin/pageadmin.py` 4/5 reps — a
  seed!). The model over-weighed graph context and under-selected
  straightforward targets.

## 7. Interpretation (committed questions)

- **Where does Graph help?** Precision and FP control: C1 FP −19, precision
  +9.2pp; F1 improves in 3/6 scenarios (S004 0.889→0.976, S008 0.741→0.889,
  S006 0.278→0.414).
- **Where does Graph hurt?** Recall in wide-scope scenarios (S007 −20pp;
  S005 −16pp) and FN overall (14→24). The soft-evidence arm over-prunes.
- **Does it reduce FN?** No — C1 increases FN (+10). This is the headline
  negative. Only the (nearly non-compliant) C2 mechanism recovered FN in the
  single S006 run it completed.
- **At what FP/token cost?** FP control improves (−19) but token cost
  roughly triples (+5,458 mean total tokens/cell) because the full 562-edge
  graph is in the prompt; C2 2-hop carries even larger prompt overhead
  (+1,853 vs C0).
- **Is soft evidence ignored?** No — it is heavily used, but as a
  **conservative pruning signal**, not as a recall amplifier. The model's
  behavior changed strongly (FP −19, selections 147→118), demonstrating
  uptake, but in the "wrong" direction for the FN objective.
- **Does mandatory disclosure repair missed structural neighbors?** In the
  one C2-1hop S006 run that complied: yes (R 1.0). Across the arm: no —
  compliance collapsed (2/30), so the mechanism could not operate.
- **How sensitive to hop distance?** Directly and negatively: zone size
  25–41 (1-hop) → 111–119 (2-hop) drove compliance from 2/30 to 0/30.
  3-hop (129–130) was pre-registered infeasible and not run.
- **S006 improve, and why?** Yes, partially (F1 0.278→0.414) — through
  precision gains, not neighbor recovery; the structural miss
  (`plugins.py`) persists under soft evidence and is only recovered by the
  (rarely-compliant) mandate.
- **Another scenario worse, and why?** S007 — cross-cutting scope is the
  worst case for the conservative shift induced by graph hints.

## 8. Overall classification (pre-registered, no universal graph claim)

| Axis | Classification | Rationale |
|---|---|---|
| **GRAPH HINT SIGNAL** | **MIXED** | Improves precision (+9.2pp), FP (−19), F1 in 3/6 scenarios; but RECALL −8.3pp, FN +10 (the primary M3 objective moved backward), tokens ×3. Soft evidence behaves as a pruning signal, not a recall amplifier. |
| **GRAPH-GATED DISCLOSURE** | **NOT PROMISING (as implemented)** | Mandatory-zone compliance 2/30 (1-hop) → 0/30 (2-hop); the sparse schema's natural output length is far below the in-zone mandate. The mechanism cannot repair missed neighbors if the model does not comply. The one compliant S006 run is suggestive, not evidence. |

**No universal graph claim is made.** Graph Hints is a precision/FP
intervention with a recall penalty; Graph-Gated Disclosure is operationally
infeasible under the frozen sparse contract at these zone sizes.

Evidence: `research/graph-c0-c1-c2-01/` (run_records.jsonl, raw + SHA
sidecars, final_metrics.json, interpretation.json, closure_gates.json,
prestudy_gates.json, manifest_90.json, seed_zone_identity.json,
graph_verification.json, c0_reuse.json). Companion reports:
`M3_GRAPH_SCENARIO_FAILURE_TAXONOMY.md`, `M3_GRAPH_HOP_SENSITIVITY.md`,
`M3_GRAPH_COST_RECALL_TRADEOFF.md`.