# M1 Scenario-Level Analysis

**Milestone:** M1 defensive closure (M1A + M1B evidence)
**Date:** 2026-09-13
**Evidence:** audited M1B controlled 16K encoding ablation, 6 scenarios x
(Full-v2, Sparse-v2) x 5 repetitions; per-scenario numbers below are pooled
micro over the 5 valid repetitions of each arm (all 60 cells valid).
**Computation:** zero scientific API calls.

Scenario key (S002..S008 = `djangocms-external-validity-002..008`).

Gold write sets (evaluation-only): S002 `cms/api.py` (1); S004
`cms/models/contentmodels.py`, `cms/admin/pageadmin.py`, `cms/views.py`,
`cms/api.py` (4); S005 `cms/models/permissionmodels.py`,
`cms/utils/page_permissions.py`, `cms/admin/permissionadmin.py`,
`cms/admin/pageadmin.py`, `cms/cms_toolbars.py` (5); S006
`cms/models/pluginmodel.py`, `cms/admin/placeholderadmin.py`,
`cms/utils/plugins.py` (3); S007 (7); S008 (4).

---

## 1. Per-scenario table (Full-v2 vs Sparse-v2)

Legend: P = precision, R = recall, F1 = harmonic mean, FNR = miss rate,
records = serialized decision rows per run (Full-v2 always 144; Sparse-v2 =
emitted non-PRESERVE rows), comp = mean completion tokens, cost = mean
recorded API cost per run, lat = mean latency seconds, fullR = fraction of 5
runs with full recall.

### S002 (single-file loc change; easiest case)

| Arm | validity | trunc | sel | TP | FP | FN | P | R | F1 | FNR | fullR | records | comp | cost | lat |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Full-v2 | 5/5 | 0 | 5 | 5 | 0 | 0 | 1.000 | 1.000 | 1.000 | 0.000 | 1.0 | 144.0 | 7,865 | $0.00862 | 41.1 |
| Sparse-v2 | 5/5 | 0 | 6 | 5 | 1 | 0 | 0.833 | 1.000 | 0.909 | 0.000 | 1.0 | 1.2 | 486 | $0.00125 | 7.2 |

Both arms saturate recall. Sparse costs -93.8% completion tokens and -85.5%
cost for a small precision loss (one spurious selection across the 5 runs).
S006-free scenario; Sparse slightly worse on precision here too.

### S004 (model + admin + views + api change)

| Arm | validity | trunc | sel | TP | FP | FN | P | R | F1 | FNR | fullR | records | comp | cost | lat |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Full-v2 | 5/5 | 0 | 28 | 17 | 11 | 3 | 0.607 | 0.850 | 0.708 | 0.150 | 0.6 | 144.0 | 8,294 | $0.00907 | 67.5 |
| Sparse-v2 | 5/5 | 0 | 25 | 20 | 5 | 0 | 0.800 | 1.000 | 0.889 | 0.000 | 1.0 | 5.0 | 861 | $0.00164 | 25.4 |

Sparse strictly dominates: recall 1.0 vs 0.85, F1 0.889 vs 0.708, FN 0 vs 3,
cost -81.9%.

### S005 (permissions / admin / toolbar change)

| Arm | validity | trunc | sel | TP | FP | FN | P | R | F1 | FNR | fullR | records | comp | cost | lat |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Full-v2 | 5/5 | 0 | 43 | 20 | 23 | 5 | 0.465 | 0.800 | 0.588 | 0.200 | 0.4 | 144.0 | 8,417 | $0.00921 | 37.8 |
| Sparse-v2 | 5/5 | 0 | 28 | 25 | 3 | 0 | 0.893 | 1.000 | 0.943 | 0.000 | 1.0 | 5.6 | 853 | $0.00165 | 4.8 |

Sparse strictly dominates: F1 0.943 vs 0.588, FN 0 vs 5, FP 3 vs 23, cost
-82.1%. Largest semantic gain in the study.

### S006 (plugin model + placeholder admin + plugin utils change) — the counterexample

| Arm | validity | trunc | sel | TP | FP | FN | P | R | F1 | FNR | fullR | records | comp | cost | lat |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Full-v2 | 5/5 | 0 | 39 | 12 | 27 | 3 | 0.308 | 0.800 | 0.444 | 0.200 | 0.4 | 144.0 | 8,508 | $0.00928 | 38.8 |
| Sparse-v2 | 5/5 | 0 | 21 | 5 | 16 | 10 | 0.238 | 0.333 | 0.278 | 0.667 | 0.0 | 4.2 | 869 | $0.00165 | 23.9 |

**S006 is a direct counterexample to any claim that Sparse universally
improves semantic selection.** Here Sparse-v2 is markedly WORSE: recall 0.333
vs 0.800, F1 0.278 vs 0.444, FN 10 vs 3, FNR 0.667 vs 0.200, and zero
full-recall runs in either arm. Only cost improves (as always). Sparse-v2
systematically misses `cms/utils/plugins.py` (and under-selects
`cms/admin/placeholderadmin.py`), while Full-v2's broad over-selection
recovers 7 of the 10 gold files Sparse misses. See the S006 deep diagnosis
below.

### S007 (cross-cutting: models + admin + permissions + toolbar + api + signals)

| Arm | validity | trunc | sel | TP | FP | FN | P | R | F1 | FNR | fullR | records | comp | cost | lat |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Full-v2 | 5/5 | 0 | 51 | 24 | 27 | 11 | 0.471 | 0.686 | 0.558 | 0.314 | 0.0 | 144.0 | 8,532 | $0.00933 | 50.3 |
| Sparse-v2 | 5/5 | 0 | 33 | 31 | 2 | 4 | 0.939 | 0.886 | 0.912 | 0.114 | 0.2 | 6.6 | 939 | $0.00175 | 28.8 |

Sparse dominates on precision (0.939 vs 0.471) and F1 (0.912 vs 0.558) but has
2 fewer TP; recall 0.886 vs 0.686. FN 4 vs 11. Largest precision gain.

### S008 (cache / signals / toolbar middleware / template tags)

| Arm | validity | trunc | sel | TP | FP | FN | P | R | F1 | FNR | fullR | records | comp | cost | lat |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Full-v2 | 5/5 | 0 | 40 | 15 | 25 | 5 | 0.375 | 0.750 | 0.500 | 0.250 | 0.0 | 144.0 | 8,682 | $0.00951 | 96.3 |
| Sparse-v2 | 5/5 | 0 | 34 | 20 | 14 | 0 | 0.588 | 1.000 | 0.741 | 0.000 | 1.0 | 6.8 | 846 | $0.00168 | 31.6 |

Sparse strictly dominates: recall 1.0 vs 0.75, F1 0.741 vs 0.500, FN 0 vs 5,
cost -82.4%.

## 2. S006 deep diagnosis (why does Sparse fail here?)

- **Gold.** `cms/models/pluginmodel.py` (CMSPlugin model change), 
  `cms/admin/placeholderadmin.py` (admin form shows PageContent context),
  `cms/utils/plugins.py` (placeholder rendering filter). The requirement adds
  a nullable `page_content` FK to CMSPlugin and asks for queryset-level
  language filtering in placeholder rendering.
- **Full-v2 behavior.** With the whole 144-candidate universe made explicit,
  Full-v2 selects 39 files (broad): it over-selects heavily (27 FP) but
  catches 12 gold TPs including all three gold files in the pooled run set
  (12 TP / 3 FN across 5 runs).
- **Sparse-v2 behavior.** Sparse selects only 21 files, catching 5 TPs and
  missing 10 (FN). The 5-run pooled pattern shows Sparse-v2 repeatedly picks
  `cms/models/pluginmodel.py` and `cms/admin/placeholderadmin.py` but
  **misses `cms/utils/plugins.py`** — the module that actually performs the
  queryset-level language filter the requirement demands.
- **Why the miss happens.** Under Preserve-by-Omission, the model must
  positively flag each changed file against a 144-candidate universe with
  sparse (non-PRESERVE-only) output. `cms/utils/plugins.py` is a utility
  module whose connection to "CMSPlugin gains a page_content FK" is indirect
  (it is a helper that renders placeholder plugins); the sparse policy gives
  the model no structural reminder of downstream utility modules that consume
  the changed model. Full-v2's exhaustive pass, by forcing a decision for
  EVERY candidate, incidentally visits utility consumers and recovers them.
- **Consequence.** S006 shows the encoding effect is NOT monotone: sparsity
  improves precision-oriented selection (S004/S005/S007/S008) but can
  sacrifice recall of structurally-indirect change targets (S006). This is
  exactly the failure mode that a dependency graph (M3) is hypothesized to
  repair: in S006 the gold file `cms/utils/plugins.py` is a graph neighbor of
  `cms/models/pluginmodel.py` (imports from pluginmodel), so graph-gated
  disclosure (C2) will force an explicit decision on it inside the 1-hop risk
  zone. S006 is therefore the pre-registered poster case for M3's primary
  hypothesis (Graph reduces FN), and the M3 interpretation section is
  committed to reporting whether C1/C2 actually recover S006's FN or leave
  them intact.

## 3. Cross-scenario reading

- **Cost effect is universal:** in ALL 6 scenarios Sparse-v2 uses fewer
  completion tokens (mean -90.35% study-wide), fewer records, less cost
  (-82.54%) and less latency (-63.29%).
- **Semantic effect is mixed:** Sparse strictly dominates on P/F1/recall in
  S004, S005, S007, S008 (4 of 6); it is neutral-to-mixed in S002 (recall
  tied, precision down); it is WORSE in S006 (recall 0.333 vs 0.800, F1 0.278
  vs 0.444).
- **Recall risk concentrates in S006.** Pooled study-wide Sparse recall
  0.8833 vs Full 0.7750 is driven by the four dominated scenarios; S006 is the
  single scenario where Sparse recall collapses.
- **No universal semantic claim is made.** The scenario report is the unit of
  truth; the study-level aggregates in
  `reports/M1_STATISTICAL_ANALYSIS.md` (n=6, mixed signs) are the honest
  summary.

Companion: `reports/M1_STATISTICAL_ANALYSIS.md`,
`reports/M1_THREATS_TO_VALIDITY_MATRIX.md`,
`reports/m1_defensive_closure_stats.json`.