# 00_CURRENT_RESEARCH_STATE.md

**Single authoritative current-state document — POST-ICCI closure (2026-09-15).**
**This document SUPERSEDES the historical handoffs (it does NOT delete them).**
For historical closure records see `docs/PROJECT_HANDOFF.md`, `SYSTEM_STATE.md`,
`TODO.md`, `docs/PAPER_WRITING_HANDOFF.md`, `docs/MSC_RESEARCH_ROADMAP_2026_2027.md`
(all preserved verbatim below their HISTORICAL boundaries).

**CURRENT TRUTH (2026-09-20, STAGE5_V2_FINAL — FINAL THESIS IMPACT-LOCALIZATION
FREEZE + ONE-SHOT STAGE-5 CONFIRMATORY EVALUATION; verdict
`STAGE5_V2_FINAL_CONFIRMATION_FAIL` + `IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED`;
the frozen DEV-selected V2 policy did NOT survive the untouched confirmatory
evaluation; method-search phase CLOSED):**
→ **P84 governance (approved by Ahmed) + full preregistration frozen BEFORE
unsealing:** candidate = `PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2`
(`BEST_FROZEN_DEV_CANDIDATE_NOT_CONFIRMED_SUPERIOR_ON_BOTH_REPOS`); population
EXACTLY djangoCMS RESERVE 59 + Saleor INTERNAL_TEST 80 = 139
(`SALEOR_RESERVE_POWER_EXTENSION = NO`); `QWEN_REALIZATION = A`; final V2
deployment model refit on ALL 323 DEV (L2-LR C=1.0 liblinear max_iter=1000
random_state=0; threshold 0.20 via 5-fold task-grouped OOF argmax pooled
micro-F1, tie-break HIGHER; config_sha256 `8925d29a…`); preregistration
committed `4badcea1…`, pushed, tagged `stage5-v2-final-preregistered-2026-09-20`
BEFORE any Stage-5 outcome (commit==tag peel==origin/main==HEAD `4badcea1`);
`STAGE5_IRREVERSIBLE_CHECKPOINT_REACHED` printed; primary endpoint =
repo-stratified pooled micro-F1 diff (V2 minus Sparse), 10,000 resamples seed
20260920, CI95 [Q2.5,Q97.5]; success rule A (pooled delta>0 AND CI lower>0) AND
B (dc point delta>0 AND saleor point delta>0); per-repo CIs secondary,
non-gating.
→ **Stage-5 execution (one-shot; paid cost $0.544067 << $1.00 ceiling; live
price verified):** all 139 case bundles materialized (zero-API; dc RESERVE 59 +
saleor IT 80; hidden proxies present); Sparse write sets generated with the
frozen Sparse-v2 strategy (qwen3-coder, 139/139 succeeded, schema-valid,
1,702,783 tokens, $0.544009); Qwen query embeddings 5,827 tokens $0.000058 (all
41,996 Stage-5 code units already in the persisted realization-A E: cache -> no
corpus re-embed); parent-only memory built for all 139; frozen V2 model +
threshold 0.20 applied.
→ **PRIMARY RESULT (audited 10/10):** pooled V2 F1 0.2269 vs Sparse 0.2857;
**Delta F1 = −0.0588, 95% CI [−0.1119, −0.0084]** (excludes zero, negative);
**criterion A FAIL** (point<0, CI lower<0); **criterion B FAIL** (djangoCMS
point delta −0.0618 < 0 AND Saleor point delta −0.0570 < 0). **Verdict
`STAGE5_V2_FINAL_CONFIRMATION_FAIL`.** Both repositories point in the same
negative direction: the DEV V2 improvement did not transfer; on untouched
evidence Sparse is BOTH more precise and more sensitive than V2. Per-repo:
djangoCMS Sparse F1 0.3028 vs V2 0.2410; Saleor Sparse 0.2744 vs V2 0.2174.
→ **Secondary + Acc@K (descriptive, NOT gate):** set sizes mean 1.79-1.93;
additions/drops ~0.56-0.98; V2 Acc@1/3/5 (139) 0.2374/0.1223/0.1223, Hit@5
0.4748; per-repo values in `reports/stage5_secondary_result.json`.
→ **Efficiency:** paid $0.544067 total (Sparse $0.544009 + query $0.000058),
1,708,610 tokens, hard $1.00 ceiling respected; zero corpus re-embed; zero
model downloads; local memory build.
→ **Independent audit `reports/stage5_independent_audit.json` 10/10 PASS**
(recomputes task counts, Sparse/V2 TP/FP/FN, per-repo P/R/F1/FNR, pooled
stratified Delta F1 + bootstrap CI, direction consistency, Acc@K/Hit@K/Recall@K,
final label WITHOUT importing the primary analyzer). 10 pre-unsealing tests
PASS; ruff clean; py_compile clean; git diff --check clean.
→ **Stage-5 decision:** `IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED`; the
current false-negative/Sparse-recovery research question is now closed by the
untouched confirmation. Next phase (separate authorized mission):
`EXTERNAL_VALIDITY_AND_END_TO_END_REGENERATION` (cross-repo/language transfer,
downstream regeneration, Functional Correctness, Preservation, Architecture
Compliance, end-to-end efficiency). NO further localization method shopping for
the current thesis; future methods remain future work.
**PRIOR TRUTH (2026-09-20, ISSUE-GROUNDED INTENT HEADROOM — T3 minimal-cost
scientific test of whether a real pre-change issue description fixes the
information bottleneck; verdict `ISSUE_GROUNDED_INTENT_SIGNAL_NOT_SUPPORTED`
(frozen negative); strict temporal rule; kept the short commit-message proxy;
no new final policy; no V1/V2/Sparse changes; no corpus re-embed; no Stage 5;
sealed sets untouched):**
→ **P82 governance amendment + frozen protocol recorded APPEND-ONLY and BEFORE
any issue-ranking outcome inspection** (`docs/ISSUE_GROUNDED_INTENT_HEADROOM_IMPACT_DECLARATION_2026-09-20.md`
+ `reports/issue_grounded_intent_freeze.json`): primary alternative intent =
ISSUE TITLE + ISSUE BODY (PR body/diff/review/comments/target paths FORBIDDEN);
deterministic `#NNNN` parsing + repository-local resolution; provenance
categories DIRECT_ISSUE / PR_ONE_LINKED / PR_MULTI_LINKED / PR_NO_LINKED /
UNRESOLVED; multiple linked issues concatenated in ascending number order;
STRICT temporal rule (`created_at < target_time` AND `updated_at <=
target_time`; else TEMPORALLY_UNCERTAIN, descriptive only); frozen issue corpus
+ SHA256 manifest before ranking; PRIMARY paired population = same DEV task ids
in both arms; ARM M = frozen Qwen message rankings, ARM I = ONLY new issue-query
embeddings (against the persisted E: code-unit cache); unchanged file-MAX
aggregation / cosine / tie-break / full-universe dense rank; robustness vs both
realizations; metrics = target-file Recall@1/3/5/10/20 + coverage + median rank
+ MRR + rank distribution + top-K precision + exact rank movement + task-paired
bootstrap 10,000 (seed 20260920); DeepFNRescue@20 with the frozen deep-dense-miss
definition; frozen parent-only episode BM25 arm (message vs issue query);
path-mention sensitivity (descriptive, pre-registered, no task deletion);
intent-length analysis (descriptive pods); gate frozen BEFORE outcomes:
SUPPORTED needs A Recall@20(I)>Recall@20(M) AND B CI lower >0 AND C median rank
improves/equal AND D no leakage, on BOTH repos; one repo -> MIXED; neither ->
NOT_SUPPORTED.
→ **Reference verification (recomputed, NOT copied):** djangocms 99/174 and
saleor 112/149 commit messages contain `#NNNN` references (matches the prior
descriptive claim exactly); 262 refs over 211 tasks; 257 distinct repo-local
objects resolved via GitHub API (REST + GraphQL, free, cached). Provenance:
DIRECT_ISSUE 28 (dc 27 / sc 1), PR_ONE_LINKED 30 (16/14), PR_MULTI_LINKED 8
(5/3), PR_NO_LINKED 145 (51/94), NO_REFERENCE 112 (75/37). Tasks with a
resolvable issue-grounded candidate: djangocms 48, saleor 18.
→ **Strict temporal result (the dominant finding):** PRIMARY temporally-clean
paired population = **djangocms 12 / saleor 0** (12/174 = 6.9%; 0/149 = 0%).
15 clean issues across the 12 djangocms tasks; the exclusion is dominated by
`updated_at > target` (GitHub issues often updated/closed at/after the merge
commit, often only seconds later). 36 djangocms + 18 saleor tasks had
candidates but NONE clean.
→ **Headroom (djangocms clean n=12; identical in realizations A and B):**
ARM M / ARM I pooled Recall@1 0.1875/0.1875, @3 0.3438/0.3438, @5 0.4688/0.4688,
@10 0.5938/0.5625, **@20 0.6875/0.7188**; task-paired bootstrap (10,000) for
Delta Recall@20 point **+0.0201**, CI **[-0.0875, +0.1375]** (crosses zero);
pooled median target rank **6.0 -> 7.5** (worsens); MRR 0.3510 -> 0.3750; per
task mean-of-medians 21.54 -> 18.92 (improves). Rank movement per file:
13 improved / 15 worsened / 4 unchanged (A). **Gate: djangocms REPO_FAIL** (A
passes; B CI lower <=0 FAIL; C FAIL); **saleor no clean population -> cannot
demonstrate support** -> overall **`ISSUE_GROUNDED_INTENT_SIGNAL_NOT_SUPPORTED`**.
→ **DeepFNRescue@20 (frozen V1 deep miss within the primary population):**
djangocms 7 eligible (saleor 0); **1/7 moved into top20 by issue intent
(0.143)**; strong per-file improvements (e.g. cms/menu_bases.py 38->11,
cms/management/commands/subcommands/base.py 135->64) but only one crossed the
top-20 line. Historical-episode BM25 arm: ARM M candidate precision 0.0885
(113 files) vs ARM I 0.0431 (116 files) -> issue query LOWERS episodic
precision on this sample; no DeepFNRecovery gain.
→ **Path-mention sensitivity (descriptive):** 4/12 clean issue texts contain an
exact/basename target-file mention; Recall@20 with-mention M/I 0.5833/0.5833
(no change), without-mention 0.7500/0.8000 (+0.05) -> the small R20 gain is NOT
trivial explicit path disclosure. Intent length: issues median 174 words
(mean 209.6) vs messages median 11 words (mean 22.0); ~16x longer.
→ **Cost / reversibility (class GREEN / LOW):** GitHub API reads free (cached);
Qwen issue-query embeddings ONLY: **5,662 prompt tokens, $0.000057** (live
$0.01/M verified 2026-09-20 before call-1); hard ceiling $0.05 respected;
no corpus re-embed; no model download; no sealed evidence. Frozen issue corpus
323 records / 56.6 KB; SHA-256 `d43987b4f9f75ace3c26597002526d0f6579c9554cc3229425648d37ad135d0f`.
→ **Validation:** 27/27 new unit tests PASS; independent audit **12/12 PASS**
(`reports/issue_grounded_audit.json`) recomputes every claim WITHOUT importing
the analyzer; ruff clean; py_compile clean; git diff --check clean.
→ **Verdict:** `ISSUE_GROUNDED_INTENT_SIGNAL_NOT_SUPPORTED` frozen (no full
issue-grounded pipeline; do NOT rerun V1/V2 with issue text). Interpretation:
the commit-message proxy was NOT demonstrated to suppress useful localization
information under the strict temporal rule; the bottleneck is compounded by the
near-emptiness of the temporally-clean issue-grounded population (esp. Saleor).
Future roadmap (documented only, NOT executed): ENERGY_BASED_CHANGE_SET_COMPLETION
(structured prediction over file sets, LeCun-EBL reference, dedicated literature
review required) + JEPA/world-model supervisor-discussion direction.
**Stage-5 decision unchanged: `FINAL_POLICY_NOT_FROZEN`** - confirmatory stays
PAUSED and SEALED (djangoCMS RESERVE 59, Saleor INTERNAL_TEST 80, Saleor RESERVE
1086; spent djangoCMS INTERNAL_TEST untouched).
**PRIOR TRUTH (2026-09-20, PARENT-ONLY REPOSITORY MEMORY RESCUE V2 — T3
scientific continuation of the history-augmented deep false-negative recovery
line; verdict `PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_FAIL` (frozen negative);
parent-only repository-history memory as an ORTHOGONAL signal; ZERO API; sealed
sets untouched; Stage 5 stays PAUSED/SEALED):**
→ **P80 governance amendment + frozen config + Full-Universe cancellation
recorded APPEND-ONLY and BEFORE any implementation/outer-OOF inspection:**
`FULL_UNIVERSE_V2_CANCELLED_AS_NON_BINDING_ABLATION` — verified from already-
exposed V1 artifacts WITHOUT fitting a new model: V1 selected non-Sparse
additions ONLY at dense ranks 1-4 (rank1 172, rank2 93, rank3 20, rank4 3,
ranks 5-20 = 0; n=4,981 pool rows, 0 selected); max outer-OOF probability
among non-Sparse ranks 5-20 = 0.1880 (p95 0.0886) and ranks 15-20 = 0.0650
(p95 0.0428); all five V1 thresholds 0.17-0.21 strictly above → the top-20
boundary was NEVER active at the decision boundary; removing it while keeping
the rank-monotone signal would be a near-null rerun with forking-path risk.
Descriptive decision from exposed DEV/V1 artifacts, NOT a new experiment.
→ **ONE high-level hypothesis tested (ZERO API):** parent-visible repository
history contains localization signal orthogonal to current-code dense
similarity and can rescue affected files deep in the Qwen dense ranking.
→ **Deep dense misses (verified):** `DEEP_DENSE_MISS` = historical-proxy
positive file that remains a V1 false negative AND was outside the V1 frozen
candidate universe (Sparse UNION dense-top20): djangoCMS **199** / Saleor **177**;
median dense rank 62 / 70. Dependency-cluster diagnostic (descriptive
oracle-style, NEVER inference seeds, NO graph features in V2): A direct
relation to another proxy positive 109/199 and 130/177; B adjacent to V1 TP
25 and 49; C within 2 hops 56 and 76.
→ **Frozen memory generator (parent-only; fail-closed ancestry; ALL parent-
visible production-changing history; caches on D: outside Git, 33.5 MB):**
Channel A structural co-change: Jaccard = C(f,s)/(C(f)+C(s)-C(f,s)), pair
score 0 if C(f,s)<2 (frozen support 2), seeds = Sparse files + Qwen dense
rank-1 file; cochange_memory_score = max(cochange_sparse, cochange_top1).
Channel B episodic: deterministic BM25 over historical commit text (subject +
body; no web/API enrichment), query = frozen task intent,
EPISODIC_TOP_CHANGES = 10; episode_similarity(f) = max normalized BM25 among
retrieved top-10 episodes touching f (0 if none); episode_hit_count
descriptive only. log_history_change_count = log1p(C(f)). Memory candidate
set = top-10 NON-SPARSE structural ∪ top-10 NON-SPARSE episodic (union;
tie-break higher score / higher support / path ascending).
→ **Deep-FN coverage before modeling (frozen generator):** union recovery of
DEEP_DENSE_MISS by the memory candidate set: djangoCMS 43/199 (0.216;
structural 14 / episodic 23 / both 6), Saleor 48/177 (0.271; 20/24/4);
unrecovered 156/129. Sparse-empty recovery: 22/105 (0.210) / 16/69 (0.232).
Mechanism baselines (same budget): popularity 41 (0.206) / 18 (0.102); seeded
deterministic random (seed 20260920, 1000 resamples) 11.1 (0.056) / 2.45
(0.014). Memory > popularity on Saleor, >> random on both. NO 15% threshold;
preregistered V2 continued regardless.
→ **V2 result (realization A, Qwen full-file scores; EXACTLY V1 model/CV/
threshold; 11 features = 7 V1 + cochange_sparse + cochange_top1 +
log_history_change_count + episode_similarity):** djangoCMS Sparse
125/155/382 (P 0.4464/R 0.2465/F1 0.3177/FNR 0.7535) → V2 152/222/355
(P 0.4064/R 0.2998/F1 0.3451/FNR 0.7002), Delta F1 +0.0274 CI
[−0.0102, +0.0636] CROSSES ZERO; Saleor Sparse 99/193/369 (P 0.3390/R 0.2115/
F1 0.2605/FNR 0.7885) → V2 158/283/310 (P 0.3583/R 0.3376/F1 0.3476/FNR
0.6624), Delta F1 +0.0871 CI [+0.0515, +0.1229] PASS. **Primary gate FAIL**
(djangoCMS criterion B) in BOTH realizations A and B → **verdict
`PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_FAIL`** (robust FAIL; 99.07% exact
same set, mean Jaccard 0.9964). V2 point F1 improves over BOTH Sparse and V1
on BOTH repos (djangoCMS 0.318→0.334→0.345; Saleor 0.261→0.336→0.348).
→ **Error decomposition (A):** djangoCMS retained 110 / dropped 15 / FP
dropped 49 / FP retained 106; added positives 42 = 0 dense-only + 8 structural
+ 6 episodic + 28 multiple-memory (ALL added positives were history-involved);
new FP 116; remaining FN not-generated 156 / rejected 184 / Sparse-TP-dropped
15. Saleor retained 94 / dropped 5 / FP dropped 65 / FP retained 128; added
64 = 4/20/12/28; new FP 155; remaining FN 129/176/5. Set sizes: policy mean
2.15/2.96, empty-policy 37/10 (vs empty-Sparse 53/41). Sparse-empty metrics
(djangocms n=53: F1 0.062; Saleor n=41: F1 0.245). Intent stratification
(descriptive, NOT a feature/gate): short intents (<=6 words) are hardest on
DEV (djangocms <=6 F1 0.209 vs >15 0.432; Saleor <=6 0.276 vs >15 0.402);
hypothesis-generating only, no causal/information-theoretic claim.
→ **Channel ablations (descriptive; NOT used to redefine V2):** structural-
removed F1 0.3459/0.3333; episodic-removed 0.3462/0.3326; FULL V2 0.3451/
0.3476 — each channel adds a small descriptive amount on Saleor; verdict
unchanged everywhere.
→ **Determinism (gate G):** 2 reruns identical (SHA 4e2c880…). Independent
audit **23/23 PASS** (recomputes every claim from artifacts WITHOUT importing
the analyzer). New unit tests **36/36 PASS**; V1 calibrated suite 18/18 still
PASS. Efficiency: 0 API calls / $0.00; history build ≈ 183 s one-time;
classifier ≈ 25-40 s/realization; D: cache 33.5 MB (outside Git).
→ **Future hypotheses documented, NOT executed:** `INTENT_ADAPTIVE_SELECTIVE_
LOCALIZATION` (abstain/broaden when confidence low; risk-coverage evaluation)
added to the roadmap; `PROVENANCE_BY_CONSTRUCTION` strategic note
(`reports/PROVENANCE_BY_CONSTRUCTION_DIRECTION_NOTE_2026-09-20.md`) created
(`SUPERVISOR_DISCUSSION_REQUIRED_BEFORE_EXECUTION`; NOT a scope change).
→ **Verdict:** `PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_FAIL` frozen (no
automatic V3; any V3 needs a NEW mission + NEW frozen hypothesis).
Interpretation: parent-visible repository history IS an orthogonal real
zero-API signal (it recovers deep dense misses at the candidate level), but
the unchanged final-set gate still fails on djangoCMS. **Stage-5 decision:**
`FINAL_POLICY_NOT_FROZEN` — confirmatory stays PAUSED and SEALED (djangoCMS
RESERVE 59, Saleor INTERNAL_TEST 80, Saleor RESERVE 1086; spent djangoCMS
INTERNAL_TEST untouched). No novelty claim (repository-memory is prior art,
arXiv 2510.01003).

**CURRENT TRUTH (2026-09-20, CALIBRATED SET SELECTION V1 — T3 scientific
continuation of the two-realization line; verdict
`CALIBRATED_SET_SELECTION_V1_FAIL` (frozen negative); DEV-ONLY FINAL FILE-SET
POLICY; ZERO API; sealed sets untouched; Stage 5 stays PAUSED/SEALED):**
→ **P78 governance amendment + frozen config recorded APPEND-ONLY and BEFORE
any outer-OOF inspection:** `INDEPENDENT_DENSE_RETRIEVAL_REPLICATED` means lack
of independent replication is NO LONGER a Stage-5 blocker; Stage 5 remains
paused because **`FINAL_POLICY_NOT_FROZEN`**; the pretrained-model provenance
claim boundary preserved (independent replication weakens, does NOT eliminate,
the possibility that a pretrained model saw public target-repository code;
verdict C unchanged).
→ **ONE minimal interpretable repository-independent decision policy
evaluated (ZERO API):** candidate universe = Sparse files (KEEP/DROP) UNION
top-20 NON-SPARSE files by the frozen Qwen dense rank (TOP_ADD_UNIVERSE=20,
no fixed B, no max-additions cap, no min-one-file); features EXACTLY
[dense_file_score (NaN imputed to min_finite-1), log_rank=log1p(ABSOLUTE
dense_rank), gap_to_top1, in_sparse, log_sparse_set_size, sparse_empty,
sparse_rank_interaction]; L2-LR (C=1.0, liblinear, max_iter=1000, seed 0) +
StandardScaler on the 5 continuous features fit on training rows ONLY; nested
5-fold OUTER task-grouped repo-stratified CV + 5-fold INNER task-grouped OOF
threshold selection (grid 0.01..0.99 step 0.01, argmax pooled micro-F1,
tie-break HIGHER); final set = {candidate: P ≥ threshold}; primary baseline =
Sparse; paired task bootstrap (10,000 resamples, seed 20260920).
→ **Result (realization A, Qwen full-file scores):** djangoCMS Sparse
TP/FP/FN 125/155/382 (P 0.446/R 0.247/F1 0.318/FNR 0.753) → policy 140/191/367
(P 0.423/R 0.276/F1 0.334/FNR 0.724), Delta F1 +0.0165 CI [−0.0190,+0.0525];
Saleor Sparse 99/193/369 (P 0.339/R 0.212/F1 0.261/FNR 0.788) → policy
147/261/321 (P 0.360/R 0.314/F1 0.336/FNR 0.686), Delta F1 +0.0751 CI
[+0.0416,+0.1083]. **Primary gate FAIL** (both realizations A and B fail the
SAME criterion): djangoCMS criterion B (paired-bootstrap 95% CI lower for
Delta F1) crosses zero; Saleor PASSES (A-E all pass). Fold criterion E:
djangoCMS 3/5, Saleor 4/5 (A). **PARETO_SUCCESS = FALSE** (Saleor Pareto-only).
→ **Realization-B robustness (same frozen pipeline):** exact same selected
set 83.28%; mean Jaccard 0.9284 (median 1.0, min 0.0); F1 A vs B djangoCMS
0.334 vs 0.341, Saleor 0.336 vs 0.332; verdict agreement SAME (both FAIL).
→ **Error decomposition (realization A):** djangoCMS Sparse TP retained 111 /
incorrectly dropped 14 / Sparse FP dropped 44 / retained 111 / omitted
positives added 29 / new FP added 80; Saleor 93/6/57/136/54/125. F1 gain
comes from BOTH dropped Sparse FPs and added omitted positives.
→ **Set-size analysis (A):** mean |Sparse| 1.61/1.96 → mean |Policy| 1.90/2.74;
empty Sparse 53/174, 41/149; empty Policy 45/174, 12/149; mean additions/task
0.63/1.20 (no fixed B).
→ **Calibration (outer OOF, frozen 10 equal-width bins):** Brier 0.064,
ECE 0.0057 — the LR probabilities are well calibrated; reliability table
tracks closely.
→ **Oracle gap after V1 (dated successor `reports/CURRENT_ORACLE_GAP_EXPLAINED_2026-09-20.md`):**
remaining policy FN decomposes into ranking/candidate-coverage error 199/177,
ADD decision error 154/138, DROP decision error 14/6, plus proxy ambiguity.
First-pass recall/coverage remains the dominant loss.
→ **Lipton et al. 2014 note:** used as THEORETICAL MOTIVATION only (t=F1*/2
for well-calibrated probabilities); chosen thresholds (0.17–0.21) are below
the descriptive F1*/2 (0.21–0.23) — reported descriptively; NOT applied to raw
scores/ranks.
→ **POST-HOC verification correction:** the historical two-realization report
listed SweRank rank-4/5 hit rates as djangoCMS 0.023/0.034 / Saleor
0.074/0.034; fresh recomputation from the SAME artifact gives djangoCMS
0.080/0.052 / Saleor 0.134/0.094. Ranks 1-3 (used by every frozen conclusion)
are IDENTICAL; no frozen conclusion changed (transcription error noted).
→ **Competitors documented, NOT run** (`reports/LOCAGENT_MATCHED_COMPARISON_PROTOCOL_DRAFT_2026-09-20.md`):
LocAgent F1≈0.333 came from a DIFFERENT exposed 10-task population and is NOT
comparable; matched-comparison protocol drafted (same tasks/evaluator/
universe/proxy/metrics; fail-closed + usable-only separately; tokens/calls/
cost/latency); NO claim the current method beats LocAgent.
→ **Verdict:** `CALIBRATED_SET_SELECTION_V1_FAIL` frozen (no automatic V2;
any V2 needs a NEW mission + NEW frozen hypothesis). **Stage-5 decision:**
`FINAL_POLICY_NOT_FROZEN` — confirmatory stays PAUSED and SEALED (djangoCMS
RESERVE 59, Saleor INTERNAL_TEST 80, Saleor RESERVE 1086; spent djangoCMS
INTERNAL_TEST untouched). The dense-mechanism replication is complete and
accepted, but the final-set decision policy is not solved on DEVELOPMENT.
**CURRENT TRUTH (2026-09-19, QWEN3 TWO-REALIZATION REPLICATION — T3 scientific
continuation of the contamination bridge COMPLETE; verdict
`INDEPENDENT_DENSE_RETRIEVAL_REPLICATED`; full label-free file-score tables
persisted for the future calibrated ADD+DROP study; sealed sets untouched;
Stage 5 PAUSED/SEALED):**
→ **P74 amendment + P75 budget v2 + P76 wall-ceiling extension recorded
append-only BEFORE the target-aware Qwen P/R/F1 inspection:** two complete
independent realizations (A and B) of the hosted Qwen embeddings
(`qwen/qwen3-embedding-8b` @ **DeepInfra**, live $0.01/M re-verified, fallback
disabled) replace the strict bitwise-determinism requirement for the bridge
conclusion. P73 (determinism STOP) remains a valid historical record; the
protocol amendment deliberately moves to CONCLUSION REPRODUCIBILITY.
→ **FULL legal DEVELOPMENT population embedded TWICE** (49,703 embeddable
code units + 323 queries per realization; whitespace-only units excluded per
frozen §12.9; deterministic ordering; resume-safe chunked caches on E:).
Actual usage: A ≈ $0.1971, B ≈ $0.2188; cumulative (incl. ~$0.023 prior
probes) ≈ **$0.439 < $0.50 ceiling**; 0 permanent failures (2 transient 429s
retried per policy and resumed).
→ **VERDICT = `INDEPENDENT_DENSE_RETRIEVAL_REPLICATED`:** realizations A and B
BOTH pass the frozen replication gate on djangoCMS AND Saleor @B=5. Qwen F1
djangoCMS 0.226→**0.262**, Saleor 0.237→**0.270** (vs frozen Route-B); every
file-level paired-bootstrap 95% CI excludes zero on both repos in both
realizations (final F1 Δ djangoCMS +0.0362 CI [0.0134, 0.0592]; Saleor
+0.0333 CI [0.0042, 0.0616]). **Reproducibility A-vs-B (B=5, 323 tasks):
97.21% exact same selected set; mean Jaccard 0.9907; median 1.0; min 0.6667;
9 one-file boundary flips — ALL swapped one FP for another FP (pooled
metrics identical A vs B, Δ=0.0000 on every metric).** The dense ranking
signal now has **independent support** as a general mechanism.
→ **NO OVERCLAIM:** Qwen improves dense ranking/recovery over Route-B but does
NOT beat Sparse final-set F1 (0.318/0.261) and does NOT replace
SweRankEmbed-Small (0.280/0.288) — the frozen SweRank evidence stays explicit
(see the report §7). SweRank diagnostic B=1 (0.348/0.304) remains diagnostic,
NOT the primary point.
→ **NEW ENGINEERING ARTIFACT — full-file score tables:** label-free zstd
Parquet per realization (`research/contamination-bridge/qwen_embed/realization_{A,B}/full_file_scores.parquet`,
1.13 MB, 143,852 rows each; case_id/repository/parent_commit/file_path/
dense_file_score/dense_rank/in_sparse/query_sha256/model_id/provider/
realization_id). Purpose: the future DEV-only calibrated ADD+DROP study —
NO extra embedding run needed later. No target labels; evaluation joins
labels AFTER ranking is frozen.
→ **POST-HOC set-selection diagnosis verified** from source artifacts: SweRank
exact-rank omitted-positive hit rates djangoCMS 0.241/0.132/0.109 and Saleor
0.262/0.174/0.128 (ranks 1/2/3); mean |Sparse| 1.61/1.96, mean |proxy changed
set| 2.91/3.14, Sparse empty 53/174 and 41/149 — the dense signal is useful
but a fixed addition budget creates an increasing FP tail (rank hit-rates are
frequencies, NOT calibrated probabilities).
→ **CALIBRATED_SET_SELECTION_V1 DRAFTED, NOT EXECUTED**
(`docs/CALIBRATED_SET_SELECTION_V1_DRAFT.md`): minimal L2-LR feature set
(dense score/rank/gap/in_sparse/|Sparse|), grouped task-level OOF
probabilities on DEV, F1 threshold derived only inside training folds, ADD and
DROP permitted, no "min one file" constraint. **Lipton et al. 2014
F1-threshold theory documented as theory motivation only** (t = F1*/2 for
well-calibrated probabilities; NOT applied to raw cosine/rank/frequencies).
→ **Competitors documented, NOT run:** LocAgent (Acc@k not comparable with
set-based P/R/F1), Agentless, Loc-Bench (future external-validity benchmark
after the policy is frozen).
→ **Stage-5 decision unchanged: `STAGE5_REMAINS_BLOCKED_BY_PROVENANCE_OR_
NONREPLICATION`** — confirmatory stays PAUSED and SEALED (djangoCMS RESERVE
59, Saleor INTERNAL_TEST 80, Saleor RESERVE 1086; spent djangoCMS
INTERNAL_TEST untouched). The dense-replication result strengthens the
dense-mechanism hypothesis but does NOT prove unseen generalization (SweRank
provenance verdict C unchanged) and does NOT by itself unlock Stage 5.
**CURRENT TRUTH (2026-09-19, QWEN3 BRIDGE PROBE-DEFECT CORRECTION — probe
corrected, availability confirmed, then STOPPED on determinism; T3 DEVELOPMENT;
~$0.023 technical spend; Stage-5 PAUSED; sealed sets untouched):**
→ **P72 `QWEN3_EMBED_AVAILABILITY_PROBE_DEFECT_CONFIRMED`:** the original P71
"model unavailable" verdict was caused by probing the GENERATION catalog. The
dedicated embeddings catalog (`GET https://openrouter.ai/api/v1/embeddings/models`)
lists **33 embedding models**, including **`qwen/qwen3-embedding-8b`** (context
32,768; HF Qwen/Qwen3-Embedding-8B). Pinned provider **DeepInfra** at the
documented **$0.01/M** (Nebius also $0.01/M; SiliconFlow $0.04/M); fallback
disabled. Expected full-run cost `21,882,529 / 1e6 × $0.01 = $0.2188` (ceiling
$0.50). P71 remains the true historical record of the defective probe.
→ **P73 STOPPED ON MATERIAL EMBEDDING NONDETERMINISM (BEFORE the full
scientific run):** the frozen determinism probe found cosine drift ~1.0e-4
(float-level; unit top-10 overlap 1.0), but the FILE-level stability check (5
complete djangoCMS DEV tasks, two independent realizations) showed a **B=5
file-set flip on 1/5 tasks** (overlap 0.8). Per the frozen pre-committed
criterion (protocol §12.8) this is material enough to destabilize the
operating-point ranking → **STOP**. The bridge remains
**`QWEN3_EMBED_BRIDGE_TECHNICALLY_INCONCLUSIVE`** (root cause: determinism; not
unavailability). NO full scientific Qwen result was produced; technical probes
only (~$0.023); no substitute model executed. **Stage-5 decision unchanged:
`STAGE5_REMAINS_BLOCKED_BY_PROVENANCE_OR_NONREPLICATION`** — confirmatory stays
PAUSED and SEALED (djangoCMS RESERVE 59, Saleor INTERNAL_TEST 80, Saleor
RESERVE 1086; spent djangoCMS INTERNAL_TEST untouched). Recommended next
(determinism-controllable LOCAL control, e.g. BAAI/bge-m3 local inference)
requires new authorization. Human-readable consolidation + TRUE LIGHT export
delivered (export contributor report: 50 MB target unreachable without deleting
authoritative dataset/raw evidence; pilot-kaggle-upload.zip archived
externally).
**CURRENT TRUTH (2026-09-19, CONTAMINATION-ROBUSTNESS BRIDGE — scope change;
T3 DEVELOPMENT; ZERO paid API; Stage-5 confirmatory PAUSED; sealed sets
untouched):**
→ **STAGE 5 CONFIRMATORY EXECUTION PAUSED — pending DEVELOPMENT-only
contamination-robustness bridge.** The user authorized a DEVELOPMENT-only
control: does an independently pretrained dense embedding model reproduce the
SweRank DEV gain under the exact same parent-only protocol? Designated model
`qwen/qwen3-embedding-8b` via the OpenRouter embeddings interface with a hard
$0.50 scientific cost ceiling.
→ **BRIDGE STOPPED BEFORE CALL 1 = `QWEN3_EMBED_BRIDGE_TECHNICALLY_INCONCLUSIVE`
(P71, 2026-09-19):** preflight verification found (1) the exact model is NOT
available on OpenRouter (447-model catalog, **0 embedding-capable models**;
404 on qwen3-embedding-8b/4b/0.6b); (2) the required full DEVELOPMENT
population (49,705 units = 21,870,401 unit tokens + 12,128 query tokens,
Qwen3-Embedding-8B tokenizer) projects **>$0.50 at every realistic price**
($1.09–$5.47 at $0.05–$0.25/M), and subsampling is forbidden without a
documented limitation + new authorization. **NO scientific call was made (0
calls, $0.00); no substitute model was executed.** Frozen protocol + budget +
mock-tested OpenRouter client + sealed-data guard + independent preflight
audit (9/9) delivered. **Provenance audit V2** (2026-09-01 top-PyPI dump,
full SweRank repo history, paper text): django-cms rank **11,118** (just
outside the top-11k SweLoc cutoff; 2025 rank unverifiable → cannot rule out),
saleor absent from top-15k (unlikely, not impossible), no released SweLoc
manifest found anywhere. **Verdict C UNCHANGED**
(`TRAINING_PROVENANCE_INSUFFICIENT_TO_RULE_OUT_OVERLAP`) — SweRank results
remain an EXTERNAL PRETRAINED DIAGNOSTIC BASELINE, NOT clean unseen
generalization. **Stage-5 decision: `STAGE5_REMAINS_BLOCKED_BY_PROVENANCE_OR_
NONREPLICATION`** — confirmatory stays PAUSED and SEALED (djangoCMS RESERVE 59,
Saleor INTERNAL_TEST 80, Saleor RESERVE 1086; spent djangoCMS INTERNAL_TEST
untouched). Recommended alternative control (NOT executed, needs new
authorization): local `BAAI/bge-m3` under a new freeze.
**CURRENT TRUTH (2026-09-19, STRONG LOCALIZATION SIGNAL BRIDGE — T3 DEVELOPMENT
mission COMPLETE; ZERO API; Stage-4b closed with descriptive statistics; new
specialized embedding diagnostic PASSES its frozen gate; P65–P67 immutable;
sealed sets untouched):**
→ **STAGE-4b STATISTICAL CLOSURE (2026-09-19; ZERO API; POST-HOC DESCRIPTIVE
DEVELOPMENT ANALYSIS):** the frozen Stage-4b verdict
**`PRECISION_SAFE_ACCEPTANCE_FAIL` is UNCHANGED** (`reports/STAGE4B_STATISTICAL_
CLOSURE_2026-09-19.md`, `reports/stage4b_bootstrap_ci.json`). Task-paired
bootstrap (10,000 resamples, fixed seed 20260919, task unit) reproduces the
frozen point estimates EXACTLY (djangocms macro ORR 0.2225→0.1523, F1
0.2176→0.2604; saleor 0.1278→0.2029, F1 0.1744→0.1972 @B=5). CI summary:
djangocms ORR Δ−0.0702 [−0.196, +0.034] (crosses 0), final P Δ+0.0716 [0.009,
0.151] (excl 0), F1 Δ+0.0427 [−0.013, +0.096]; saleor ORR Δ+0.0751 [0.004,
0.175] (excl 0), recall Δ+0.0392 [0.009, 0.076] (excl 0). **djangoCMS
phenomenon EXPLAINED from raw task data:** macro ORR is a per-task-ratio mean,
so the conservative verifier's over-rejection of the three M=1 easy recoveries
(three Δ=−1.0 task deltas) dominates the macro, while pooled TP/FP/FN/F1/P
still improve because Arm B cuts the FP tail (40 vs 64 selected; cand-prec
0.141→0.250) and recovers the same net FNs (9→10). Pooled Recall/F1 can rise
while macro ORR falls — a macro-vs-pooled weighting artifact, not a sign the
Arm-B final set is worse at file level. This does NOT alter P67.
→ **DECISION `BOUNDED_CHEAP_SEMANTIC_CLOSED_FOR_NOW` (P68, 2026-09-19):** the
accumulated evidence (cheap structural bridge negative P64; bounded semantic
Stage-4 negative P65; precision-safe Stage-4b negative P67) closes the
currently tested bounded generic-Qwen prompt/verifier/threshold family FOR NOW,
narrowly scoped. No audit/reproducibility defect was found. It does NOT mean
semantic localization is impossible, specialized models are ineffective, or
fundamentally different signals are forbidden. Stage 4/4b NOT re-tuned; no
verifier-v3; no threshold sweeps.
→ **SWERANKEMBED-SMALL DEV EVALUATION = SWERANK_EMBED_PASS (2026-09-19; T3
DEVELOPMENT; ZERO API; EXTERNAL PRETRAINED DIAGNOSTIC BASELINE):** the
specialized issue-localization embedding signal was evaluated under a frozen
protocol (`docs/SWERANK_EMBED_BASELINE_PROTOCOL_FROZEN.md`, frozen BEFORE any
target-aware metric inspection; Route-B primary comparator, K=5 primary
operating point, clarification recorded before inspection) on the FULL legal
populations (djangoCMS DEV 174 + Saleor DEV 149). Pinned revision
`745d2a06103a66d3cfa600aa52fc0d3523010daa` (137M, CC-BY-NC-4.0, trust_remote_
code); frozen MAX-file adapter; parent-only queries; Route-B matched pool.
**@B=5 vs frozen Route-B:** djangoCMS F1 0.226→0.280 (+0.054), P +0.039, R
+0.089, FNR −0.089, macro ORR 0.163→0.291, candP 0.071→0.123; Saleor F1
0.237→0.288 (+0.052), P +0.038, R +0.083, FNR −0.083, macro ORR 0.237→0.327,
candP 0.106→0.158. **Every metric improves at every B on BOTH repos; all six
paired-bootstrap 95% CIs @B=5 exclude zero on BOTH repos.** Efficiency: **0
API calls, $0**, local CPU; one-time corpus encode (49,705 units) dominates
wall (~6.6 h); marginal per-task cost after indexing ~0.1 s. Independent audit
**11/11 PASS** (recomputes everything from raw JSONs without importing the
analyzer). **Frozen gate A–E PASS on BOTH repos → method FROZEN as the
candidate-ranking signal** (Sparse write set + ranked additions). Next step
(frozen selection): **A — use SweRankEmbed as the replacement candidate-ranking
signal inside the bounded architecture** (zero-API); option B (official
SweRankLLM listwise reranker, 7B LLM) is budget-planned but NOT executed
(needs a new frozen budget + authorization). **PROVENANCE LABEL:** SweLoc
training corpus overlap with djangoCMS/Saleor could NOT be ruled out
(**verdict C** — `reports/SWERANK_TRAINING_PROVENANCE_AUDIT.md`), so the result
is an EXTERNAL PRETRAINED DIAGNOSTIC BASELINE, NOT clean unseen generalization,
NOT a confirmatory claim, NOT comparable to external SWE-Bench numbers. Stage 5
confirmatory remains gated on a fresh frozen protocol + authorization.
→ **REPOSITORY-MEMORY + READINESS (2026-09-19; ZERO API):** the documented
"Saleor parent-visible history cache absent" blocker is RESOLVED — the FULL
Saleor history (22,615 commits, anchor `2c48391b` == dataset anchor) is
available locally at `dist/pilot-repo-cache/saleor`, so a parent-visible
co-change/evolution memory cache is deterministically buildable
(`reports/REPOSITORY_MEMORY_FEASIBILITY_2026-09-19.md`). Cross-language
readiness documented for TS (nestjs/nest), Java (JabRef/jabref) and Go
(prometheus/prometheus) with per-language universes and engineering gaps (no
non-Python import extractors) (`reports/CROSS_LANGUAGE_READINESS_2026-09-19.md`);
grafana/grafana true-polyglot (Go+TS) eligibility definition frozen
(`reports/POLYGLOT_REPOSITORY_FEASIBILITY_2026-09-19.md`). Competitor review
covers SweRank/SweLoc, SweRank+, LocAgent, RepoGraph, OrcaLoca, Agentless,
CoSIL, repo-memory (external numbers = literature context only)
(`reports/STRONG_LOCALIZATION_COMPETITOR_REVIEW_2026-09-19.md`). 38 new unit
tests PASS; affected suites PASS; sealed sets untouched.
**CURRENT TRUTH (2026-09-18, PRECISION-SAFE ACCEPTANCE PILOT — AUTHORIZED real
DEVELOPMENT pilot complete; 357 calls; Stage-4b of the gap-reduction ladder
closed NEGATIVE; Stage-4 + P65 + P66 immutable; sealed sets untouched):**
→ **PRECISION-SAFE ACCEPTANCE PILOT = PRECISION_SAFE_ACCEPTANCE_FAIL
(2026-09-18; DEVELOPMENT only; AUTHORIZED real run):** the user authorized the
frozen RANK→VERIFY→VARIABLE-ACCEPT protocol under the frozen budget (≤400
calls / ≤300,000 tokens / ≤$0.15 / ≤60 min, qwen3-coder, DEV only, sealed sets
sealed). Registration frozen BEFORE call 1 (60 tasks = 30 djangoCMS + 30 Saleor
DEVELOPMENT, seed 20260919, **Stage-4's 60 case_ids excluded**; pool = Route-B
top-10 ∪ reverse-1hop consumers cap 80; K=10; candidate-ID enum + uniqueness
rank schema; fixed-length boolean-vector verify schema). **Real run: 357
dispatched calls (240 Arm A + 60 rank + 57 verify; 3 rank abstentions →
fail-closed zero additions), 176,060 tokens, $0.0648, 718.8 s total wall —
ceilings
respected; sidecars 357/357 (0 mismatches); 0/357 schema-invalid dispatched
calls** (Stage-4 was 6/60 — the enum schema eliminated hallucinated paths).
Results @B=5: djangoCMS Arm A ORR 0.2225 / Arm B 0.1523 (Δ −0.0702), cand-prec
0.141→0.250, naive F1 0.218→0.260; Saleor Arm A 0.1278 / Arm B 0.2029 (Δ
+0.0751), cand-prec 0.088→0.116, naive F1 0.174→0.197. **Preregistered gate =
FAIL → PRECISION_SAFE_ACCEPTANCE_FAIL (negative frozen):** djangoCMS c1 ORR
(−0.0702 < +0.05) and c2 folds (2/5) FAIL; Saleor c1/c2 PASS; c3–c7 PASS on
BOTH repos. The precision-safe layer ELIMINATED the Stage-4 "ORR up, F1 down"
failure (F1 and candidate precision improve on BOTH repos; variable 0..K
acceptance removed the FP tail) and achieved material Saleor recovery, BUT on
djangoCMS the conservative verifier over-rejects (misses the 3 M=1 easy
recoveries Arm A got). No prompt/schema/threshold tuning. Independent audit
11/11 PASS; affected suites 53/53 (9 new + 44 prior). **Stage 4b closed
NEGATIVE; Stage 5 (freeze method + fresh confirmatory) NOT reached.** Any
future instrument that keeps the precision/F1 gains while restoring djangoCMS
ORR is a NEW protocol (e.g., calibrated acceptance criterion) with its own
freeze, sample discipline, budget, and explicit authorization.
**CURRENT TRUTH (2026-09-18, PRECISION-SAFE ACCEPTANCE FEASIBILITY + PROTOCOL
FREEZE — post-Stage-4 DEVELOPMENT analysis complete; ZERO API; Stage-4 negative
+ P65 immutable; sealed sets untouched):**
→ **PRECISION-SAFE ACCEPTANCE FEASIBILITY = FAMILY JUSTIFIED, SPECIFIC FROZEN
VERIFIER NOT (2026-09-18; DEVELOPMENT only; ZERO API):** the frozen Stage-4
300-call record was decomposed (13-item failure anatomy). Findings: Arm-B
cumulative candidate precision by semantic rank is flat-low on djangoCMS
(0.125 rank1 → 0.093 rank5) and decaying on Saleor (0.346 → 0.177 → 0.153);
at B=5 Arm B adds 14/26 FNs but 119/119 FPs (cand-prec 0.105/0.179 vs Arm A
0.143/0.256); **the FP tail is an acceptance-layer failure split across BOTH
pool sources** (dc 68/51, saleor 71/48 route-B-top10 vs consumer-only); pool
cap C=40 loses **10 (dc) + 29 (saleor) FNs** (cap-40 covers 52%/54%, cap-80
66%/60%, cap-120 69%/69%); 6/6 schema-invalid Arm-B calls are non-pool-path
hallucinations and the frozen analyzer granted them **partial credit**; B=10
recovery is consistent (**5/5 positive folds BOTH repos**; Saleor mean per-task
delta +0.146) — inspection-depth signal, DEVELOPMENT motivation only. **POST-HOC
feasibility (exactly ONE principled family RANK → VERIFY → VARIABLE ACCEPT):**
the AND-rule (semantic top-K AND frozen verifier approval) improves candidate
precision (dc 0.105→0.146, saleor 0.179→0.222) and recovers Arm-B's F1 loss on
dc (0.324→0.407) but does NOT beat the frozen Route-B verifier on F1 on either
repo (dc 0.407 vs 0.414; saleor 0.263 vs 0.287) because the frozen verifier is
uncalibrated for acceptance (8.6–14% approval precision). **Explicit
insufficiency stated:** the frozen verifier never saw reverse-1hop-only
candidates — no existing record can assess a verifier on them. **Verdict: the
family is justified; the specific frozen verifier is not.** Exactly ONE next
protocol frozen (`docs/PRECISION_SAFE_ACCEPTANCE_PROTOCOL_FROZEN.md`): Sparse →
expanded pool (Route-B top-10 ∪ consumers, cap C=80 DEV-derived) → bounded
semantic ranking (1 call/task) → top-K inspection set (K=10 DEV-derived) →
strict fixed-length boolean-vector verifier (1 call/task; candidate-ID enum
schema; NO partial credit) → variable accepted additions (0..K) → final file
set; baseline = frozen Route-B verifier B∈{1,3,5,10}; fresh disjoint
DEVELOPMENT sample (seed 20260919, 30/repo, 60 Stage-4 case_ids excluded; 123
dc + 97 saleor fresh eligible remain); gate c1–c7 on BOTH repos. Budget draft
`reports/PRECISION_SAFE_ACCEPTANCE_BUDGET_FREEZE_DRAFT.md`: expected ~360 calls
/ ~140k tokens / ~$0.055; hard ceilings 400 calls / 300,000 tokens / $0.15 /
60 min; **exact authorization sentence in §7; NO API call made by this
mission**. Evidence: `reports/PRECISION_SAFE_ACCEPTANCE_FEASIBILITY_2026-09-18.md`
+ `reports/precision_safe_feasibility_metrics.json` + audit 11/11
(`reports/PRECISION_SAFE_ACCEPTANCE_AUDIT.md` + `.json`); 13/13 new unit tests
PASS; Stage-4 artifacts untouched.
**CURRENT TRUTH (2026-09-18, BOUNDED SEMANTIC EXPANSION PILOT — AUTHORIZED real
DEVELOPMENT pilot complete; 300 calls; Stage-4 of the gap-reduction ladder
closed NEGATIVE; P2 Phase-1 NEGATIVE + First-Pass Recall + Oracle-gap + ranking
bridge conclusions frozen; sealed sets untouched):**
→ **BOUNDED SEMANTIC EXPANSION PILOT = BOUNDED_SEMANTIC_NEGATIVE_FROZEN
(2026-09-18; DEVELOPMENT only; AUTHORIZED real run):** the user authorized the
frozen protocol (`docs/BOUNDED_SEMANTIC_RERANK_VERIFY_PROTOCOL_FROZEN.md`) under
the frozen budget (≤300 calls / ≤300,000 tokens / ≤$0.30 / ≤60 min, qwen3-coder,
DEV only, sealed sets sealed; cost minimization = ceilings are safety limits;
no result-based retries; no prompt tuning; no fallback provider; STOP at the
preregistered gate). Registration frozen BEFORE call 1 (60 tasks = 30 djangoCMS
DEV + 30 Saleor DEV; Arm B pool = Route-B top-10 ∪ reverse-1hop consumers, cap
40). **Real run: 300 calls (Arm A 240 + Arm B 60), 106,325 tokens, $0.0444,
553.6 s — ceilings respected; sidecars 300/300 (0 mismatches); 6 Arm B
schema-invalid calls fail-closed.** Results @B=5 (pooled file-level): djangoCMS
Arm A ORR 0.111 / Arm B 0.250, naive-F1 0.396 / 0.327; Saleor Arm A 0.334 /
Arm B 0.357, naive-F1 0.304 / 0.270. **Preregistered gate FAIL →
BOUNDED_SEMANTIC_NEGATIVE_FROZEN:** c1 (ORR >+0.05 on BOTH repos) FAILS on
Saleor (+0.023); c3 (naive final F1 not materially worse) FAILS on djangoCMS
(−0.069). Arm B raises ORR but not materially on Saleor and materially lowers
naive final F1 on djangoCMS — the protocol's forbidden "ORR up, F1 down" case.
NO prompt/schema tuning; NO result-based retries; independent audit 8/8 PASS;
affected suites 31/31. **Stage 4 closed NEGATIVE; Stage 5 (fresh confirmatory)
NOT reached.** Any future bounded semantic instrument needs a precision-safe
acceptance rule + its own explicit authorization.
**CURRENT TRUTH (2026-09-18, RANKING BRIDGE + BOUNDED SEMANTIC FREEZE — DEVELOPMENT-only
T3 study complete; ZERO API; P2 Phase-1 NEGATIVE + First-Pass Recall + Oracle-gap
conclusions frozen; sealed sets untouched):**
→ **RANKING BRIDGE = CHEAP_RANKING_CLOSED_FOR_NOW (2026-09-18; DEVELOPMENT only;
ZERO API):** Section-1 reconfirmed the frozen ranking gap EXACTLY on djangoCMS DEV
(174) + Saleor DEV (149): Route-B composite macro ORR 0.0464/0.1177/0.1633/0.2512
and 0.0775/0.1576/0.2369/0.3173; BM25-only @5 0.161/0.234; reverse-1hop oracle
availability @K=5 0.558/0.724; consumer+provider 0.605/0.802; UNION_ALL 0.725/0.870;
Oracle-Add F1@5 0.841/0.782; oracle-reviewer Route-B F1@5 0.441/0.424 — all
verification flags PASS (baseline-freeze artifact
`reports/fn_quant_ranking_bridge_baseline_freeze.json`). Section-2 evaluated exactly
THREE transparent quantitative-structural rankers (frozen before outcome inspection;
parent-visible features only): R1 BM25+RevSupport, R2 BM25+BidirSupport, R3
BM25+BidirNorm. Typed-edge support is NOT available (frozen graph = untyped
[src,dest] edges) and is documented. **Best R1 at B=5: djangoCMS +0.034 (0.197) but
Saleor −0.020 (0.217); no formula materially beats Route-B on BOTH repos (gate c1/c2
fail on all three); folds not majority positive; artifact-free; naive-F1 not clearly
worse.** Decision **CHEAP_RANKING_CLOSED_FOR_NOW** (negative frozen; NO fourth
formula). The bounded semantic middle layer is the next instrument.
→ **BOUNDED SEMANTIC RERANK/VERIFY PROTOCOL + BUDGET PREPARED, NOT EXECUTED
(2026-09-18; ZERO calls):** frozen protocol `docs/BOUNDED_SEMANTIC_RERANK_VERIFY_
PROTOCOL_FROZEN.md` (pool = Route-B top-10 ∪ reverse-1hop consumers, dedupe,
deterministic pre-order, hard cap C=40; qwen3-coder/OpenRouter temp 0 cap 512;
strict JSON; fail-closed; no result-based retries; ≤30 tasks/repo DEVELOPMENT pilot;
matched-budget Arm A Route-B verifier / Arm B expanded-pool bounded rerank / Arm C
analytic references; primary ORR + P/R/F1/FNR + Oracle-Add-gap-closed; safety: no
material F1 regression) + `reports/BOUNDED_SEMANTIC_EXPANSION_BUDGET_FREEZE_DRAFT.md`
(≤300 calls / ≤300,000 tokens / ≤$0.30 / ≤60 min hard stop; per-call reservation
ledger; **exact user authorization sentence required before any call**). NO model/API
call made.
→ **P2 / ADAPTIVE-K STATUS (2026-09-18):** P2 Phase-1 = COMPLETE, NEGATIVE, frozen;
adaptive budget is NOT the current bottleneck and is NOT active work; the
Shichao-Zhang / adaptive-k / demand-driven-k line remains FUTURE WORK and is GATED
(revisit only after a stable ranking/recovery signal — choosing k cannot rescue a
poorly ordered candidate list); line gated, not deleted.
→ **FUTURE-WORK CORRECTION (2026-09-18):** "multi-language" has TWO distinct meanings
— (A) CROSS-LANGUAGE / CROSS-REPOSITORY (different repos from different ecosystems)
vs (B) POLYGLOT SINGLE-REPOSITORY (one repository with substantial production code
in multiple languages and real cross-language change coupling). Ambiguous roadmap
wording renamed `cross-language + polyglot-repository generalization`. **`grafana/grafana`
= FUTURE feasibility candidate ONLY** (Go backend + TS frontend, documented parity
paths; NOT scientifically accepted; requires feasibility audit, per-language
production-universe definition, cross-language coupling representation, ≥60 eligible
real commits if feasible, mixed-language commit strata, no generated/vendor/test
leakage, same proxy/leakage rules).
→ **GAP-REDUCTION ROADMAP (`reports/GAP_REDUCTION_ROADMAP.md`):** Stage 1 DONE
(Sparse + Route-B recovery), Stage 2 DONE (FN anatomy; finding = availability high,
ranking bottleneck), Stage 3 THIS MISSION (quant structural bridge = negative),
Stage 4 DONE (authorized bounded semantic rerank/verify = NEGATIVE, frozen),
Stage 4b THIS MISSION (precision-safe acceptance feasibility + ONE frozen
protocol, NOT executed, ZERO API), Stage 5 freeze + fresh confirmatory if the
Stage 4b pilot succeeds, Stage 6 adaptive-k later (gated), Stage 7
generalization (cross-language + polyglot), Stage 8 repository-agent only if needed
(fair LocAgent comparison under matched protocol).
**Boundary held:** ZERO API; P2 Phase-1 NEGATIVE + Oracle-gap BIDIRECTIONAL_HEADROOM_ONLY
+ First-Pass RECALL_SIGNAL_HEADROOM_ONLY conclusions untouched; spent djangoCMS
INTERNAL_TEST never used for selection; djangoCMS RESERVE + Saleor INTERNAL_TEST/
RESERVE sealed; 12/12 new unit tests PASS + independent audit 25/25 PASS; affected
suites 35/35.
**CURRENT TRUTH (2026-09-18, FIRST-PASS RECALL BOTTLENECK — DEVELOPMENT-only
T3 study complete; ZERO API; P2 Phase-1 NEGATIVE + fixed Route-B CONFIRMED and
untouched; sealed sets untouched):**
→ **FIRST-PASS RECALL BOTTLENECK = RECALL_SIGNAL_HEADROOM_ONLY (2026-09-18;
DEVELOPMENT only; ZERO API):** baseline freeze reproduced frozen Route-B
exactly (djangocms composite macro ORR 0.0464/0.1177/0.1633/0.2512 == frozen
results). Deterministic FN taxonomy (parent-visible features; proxy = post-hoc
label only): djangoCMS (382 FN) DIRECT_LEXICAL 95, HISTORY_COCHANGE 86,
NO_OBSERVABLE_SIGNAL 87, DOWNSTREAM_CONSUMER 64, INDIRECT_2HOP 43; Saleor (369
FN) DIRECT_LEXICAL 264, DOWNSTREAM_CONSUMER 68. **S006-like indirect-utility /
downstream misses = GENERAL_PATTERN** (consumer flag 58.9%/82.1% of FNs;
direct-1hop FNs 98.6%/100% lexically silent; repo-consistent). Source-specific
oracle recall ceilings @K=5: GRAPH_REVERSE_1HOP 0.558/0.724, UNION_ALL
0.725/0.870; BM25 ceiling is budget headroom (0.929/0.881) → availability is
NOT the binding constraint. Three simple ADD queues (BM25+ReverseDependency,
+ProviderConsumerSupport, +ComplementaryUnion) defined and compared at matched
budget: **none beats Route-B** (B=5 Δ −0.011/+0.001, −0.025/−0.001,
−0.086/−0.209). Oracle-reviewer simulation: perfect reviewer F1 ≈ 0.44/0.43
@B=5 vs Oracle-Add 0.72/0.64 → **dominant remaining loss = RANKING** (not
availability, not reviewer acceptance). Progression gate FAIL on all queues →
**Decision RECALL_SIGNAL_HEADROOM_ONLY**; no verifier calls authorized. Next
instrument (future authorized mission): bounded verifier-ranked expansion of
Route-B top-B + reverse-1hop consumer pool on DEVELOPMENT. Boundary held:
ZERO API; spent djangoCMS INTERNAL_TEST never used for selection; djangoCMS
RESERVE + Saleor INTERNAL_TEST/RESERVE sealed; 19/19 new unit tests PASS +
independent audit 19/19 PASS; Route-B reproduction exact.
**CURRENT TRUTH (2026-09-18, P2 PHASE-1 + FIXED-ROUTE-B SCIENTIFIC CLOSURE —**
**ZERO new model calls; P2 Phase-1 = NEGATIVE and frozen; fixed Route-B**
**confirmatory untouched; sealed sets untouched):**
→ **A. FIXED ROUTE-B REVIEWER CLOSURE (2026-09-18; ZERO API; frozen result
unchanged):** (1) **curve-level POST-HOC characterization**
(`reports/ROUTE_B_CURVE_LEVEL_POSTHOC_CHARACTERIZATION.md` + JSON): AURC
(normalized over B∈{0,1,3,5,10}) composite **0.1553** / verifier **0.0971** /
analytic Random **0.0277**; simultaneous task-bootstrap band (4000 resamples of
the frozen task unit); per-task recovery distributions (5/25/50/75/95
percentiles); **zero-FN tasks 10/80 (12.5%) with explicit denominator handling**
(frozen macro includes them as 0; positive-only sensitivity labelled); macro +
micro at every B. The frozen macro reproduces the frozen confirmatory numbers
exactly (B=5 composite 0.165). POST-HOC label prominent; NOT preregistered.
(2) **Sparse-vs-Full causal parity audit = PARITY_VERIFIED**
(`reports/SPARSE_FULL_CAUSAL_PARITY_AUDIT.md`): Full-v2 vs Sparse-v2 match on
model/version, provider/route, parent snapshot/candidate universe, context,
temperature/decoding, reasoning mode, completion cap, tools, repetitions; the
ONLY intended difference is the serialization-policy block (frozen
`PROMPT_CONTROLLED_DIFF` PASS 10/10). (3) **Dataset operational-definition
audit** (`reports/DATASET_OPERATIONAL_DEFINITIONS.md`): exact rules for
"meaningful intent", production-source eligibility, exclusions (canonical
codes), dedup R1/R2/R3, failure/evaluable-task rules, 3-repetition aggregation,
zero-FN handling. No new dataset; thesis/reviewer clarity only.
→ **B. P2 PHASE-1 — COMMON ADAPTIVE-BUDGET HARNESS + FOUR POLICIES (2026-09-18;**
**DEVELOPMENT only; ZERO API):** common harness `src/benchmark/p2/`
(tasks/cost_model/policies/evaluate) + `scripts/p2_phase1_run.py` +
`scripts/p2_phase1_gates.py`. Frozen anchors: fixed B={1,3,5,10} composite,
fixed-B BM25, Analytic Random, Oracle, InspectAll. Measured verifier cost model
(prompt_tokens≈204.5+7.4·B; api_cost≈0.000065+0.000005·B; least-squares fit over
the 320 frozen confirmatory verifier calls; relative accounting only).
**P2-P1 score-gap, P2-P2 marginal-score, P2-P3 cost-ratio, P2-P4 learning-k
analogue implemented with constants derived on djangoCMS DEV_TRAIN only**
(tau_gap 0.10 declared; tau_marg 1.0 = 25th pct of DEV_TRAIN top-1 composite
scores; tau_energy 0.90 declared; cost-ratio grid {0.5,1.0,2.0} declared
sensitivity). **RESULTS (djangoCMS DEV 174 / Saleor DEV 149): all four
NEGATIVE** — P2-P1 stops early (B_t 1.6/1.5; ORR 0.078/0.115 ≈ half of fixed-B5);
P2-P2/P2-P4 converge to B_t ≈ 8.5–10 at fixed-B10-equivalent cost with no saving;
P2-P3 is repo-asymmetric (djangoCMS B_t=1 vs Saleor B_t≈9 at the same tau) →
**REJECTED_BY_DESIGN** (size/repo artifact). **Strong-method gate = FALSE** → the
two stronger methods (cost-sensitive expected-loss stopping; one-step/joint
ranking+budget) were **NOT implemented** (mission §4: freeze the negative; a
valid scientific result). **P2 Phase-1 decision = NEGATIVE closure**; Phase-2
candidates: NONE. Saleor INTERNAL_TEST remains sealed.
→ **C. LITERATURE LANDSCAPE EXPANSION (2026-09-18):** +15 serious verified
entries (P2-025..P2-039) added to `research/literature/p2_algorithm_landscape.csv`
(24→39) covering adaptive computation (ACT), selective prediction/abstention
(SelectiveNet, El-Yaniv & Wiener, Chow), early-exit cascades (DeeBERT),
learning-to-defer, budgeted learning, Confidence-Budget Matching, fixed-budget
ranking & selection, adaptive-kNN graph (latest Zhang-line), VOI/active search;
primary sources verified via the arXiv API where accessible; classical works
marked CLASSICAL; nothing fabricated. Landscape report §7 + literature decision
ledger updated. The expanded landscape is the Phase-2 candidate pool.
**CURRENT TRUTH (2026-09-18, AI-ASSISTED SEMANTIC AUDIT ANALYSIS CLOSURE —**
**10 frozen rater outputs validated + ingested; agreement + post-hoc sensitivity**
**+ human minimal spot-check delivered; ZERO new model calls; P2 Phase-1 =**
**NEGATIVE and frozen; fixed Route-B confirmatory untouched; sealed sets**
**untouched):**
 **CURRENT TRUTH (2026-09-18, ORACLE-GAP DECOMPOSITION + BIDIRECTIONAL SET**
**REPAIR EXPLORATION — new exploratory DEVELOPMENT line after the frozen P2**
**Phase-1 negative closure; ZERO new model calls; P2 Phase-1 NEGATIVE and**
**frozen; fixed Route-B confirmatory untouched; sealed sets untouched):**
→ **H2. ORACLE-GAP DECOMPOSITION + BIDIRECTIONAL BOUNDED SET REPAIR =
BIDIRECTIONAL_HEADROOM_ONLY (2026-09-18; DEVELOPMENT only; ZERO API):** the
file-level Oracle/F1 gap was decomposed on djangoCMS DEV (174) + Saleor DEV
(149). Confirmatory budget verified from frozen records (matches the working
diagnostic: Sparse TP=51/FP=104/FN=199 F1=0.252; verifier B=5 F1=0.2387,
acceptance precision 0.105). **Sparse baseline** djangoCMS 0.3177 (P 0.446/R
0.247), Saleor 0.2605 (P 0.339/R 0.212). **Oracle-Add ALL** caps at 0.8674 /
**0.8291** (perfect recall leaves the Sparse FP tail). **Oracle-Drop ALL**
0.3956 / 0.3492 (recall pinned). **Bidirectional** reaches F1 1.0 at
A=ALL,D=ALL; **F1=0.85 is NOT add-only-reachable on Saleor** (ceiling 0.8291)
and requires bidirectional (e.g. A=3,D=5, 2.91 inspections/task); F1=0.90
requires bidirectional on both repos. **Dominant bottleneck: FIRST-PASS RECALL
LOSS** (75–79% of proxy positives missed; Oracle-Add ALL adds +0.55–0.57 F1),
with review false-acceptance second (Route-B add-only LOWERS file-level F1 at
every B) and ranking loss third; budget loss ≈0 → **not adaptive budget**.
Observable FP-pruning signal is weak (flagged precision ≈ random control);
heuristic BBSR fails the progression gate on both repos → no new verifier
calls authorized. Decision **BIDIRECTIONAL_HEADROOM_ONLY**; next bottleneck =
first-pass recall. Sealed sets untouched; spent djangoCMS INTERNAL_TEST used
ONLY as labelled POST-HOC sanity. 16/16 new tests PASS + independent audit
PASS. Reports: reports/ORACLE_GAP_{ERROR_DECOMPOSITION,F1_CEILING_AND_BUDGET_
SURFACE,BIDIRECTIONAL_REPAIR_FINAL_REPORT,INDEPENDENT_AUDIT}.md + JSONs.
→ **H. INDEPENDENT AI-ASSISTED SEMANTIC-PLAUSIBILITY AUDIT — ANALYSIS
COMPLETE (2026-09-18; ZERO API; descriptive only, NOT human semantic gold):**
the 10 frozen rater outputs (5 ChatGPT + 5 Claude fresh-chat batches) were
validated exactly as received — 8 valid as-is; `chatgpt_batch_02` and
`chatgpt_batch_04` had syntax-only defects (unescaped inner double-quotes in
evidence strings) and received normalized syntax-only copies (originals
untouched, full content preservation verified). Agreement against the sealed
mapping: exact row agreement **0.6981** (252/361), Cohen's kappa **0.5579**
(nominal/unweighted, sklearn-verified); confusion matrix dominated by ChatGPT
`4_not_determinable`→Claude `3_incidental_tangled` (45) and
`2_related_optional`→`3_incidental_tangled` (22); abstentions 0/0;
role split historical_changed_file 0.8468 (κ 0.50) vs omitted_candidate_file
0.6320 (κ 0.31); case-level proxy_quality 0.56 / omitted_candidate_semantic_
impact 0.48 / mixed_tangled_commit 0.68. **POST-HOC sensitivity** (frozen labels
NOT altered): 15 `omitted_candidate_file` rows whose file ALSO appears in the
historical changed set (`sparse_omitted_and_historical_changed`, κ 0.17) vs 235
outside the historical diff (κ 0.26) — consistent with raters interpreting
"omitted" as "absent from the historical diff" on the ambiguous 15. Descriptive
top-ranked-vs-random relevance OUTSIDE the historical diff, per rater and never
pooled as gold: ChatGPT 0.193 vs 0.099; Claude 0.053 vs 0.008 (both raters show
top-ranked > random in the same direction). **109 disagreements + deterministic
10-row agreement sample (seed 20260918) → 119-row human minimal spot-check form
** generated (NO fabricated human judgments; NOT expert adjudication). 19/19
unit tests PASS; independent statistical audit (sklearn recompute) matches.
Explicitly recorded as an **independent AI-assisted semantic-plausibility audit /
model-based semantic sensitivity analysis**, NOT human semantic gold; the human
two-rater + adjudicator audit remains **AWAITING_HUMAN_RATINGS**.
 → **D. SEMANTIC-AUDIT HUMAN BLOCKER (2026-09-18):** package re-verified
(PACKET_INTEGRITY PASS + SYNTHETIC_DRYRUN PASS); human-action report created
(`reports/SEMANTIC_AUDIT_ACTION_REQUIRED_FROM_HUMANS.md`); scientific blocker =
**AWAITING_HUMAN_RATINGS**. No coding time spent rebuilding ready forms.
→ **E. NESTJS READINESS (2026-09-18; ZERO API):** repo reachable, stable tags
pinnable, >=60 eligible-case rule frozen, TS import extractor NOT implemented,
no local cache — blockers listed (`reports/NESTJS_READINESS_ZERO_API_2026-09-18.md`);
no inference. **F. V1.5 PATCH LIST** (`reports/V15_SUPERVISOR_PATCH_LIST.md`);
no V1.6, no PPTX.
→ **G. VALIDATION:** 6/6 T3 gates PASS + independent audit PASS
(`reports/P2_PHASE1_INDEPENDENT_AUDIT.md`, `reports/p2_phase1_gates_validation.json`);
31 new P2 tests (15 policy unit + 10 evaluator unit + 6 integration) PASS;
harness reproduces the frozen route_b_v2 / Saleor transfer fixed-B composite
macro ORR within 0.02. **Boundary held: ZERO new model calls; djangoCMS RESERVE
+ Saleor INTERNAL_TEST/RESERVE sealed; the opened djangoCMS INTERNAL_TEST used
only for frozen Route-B reporting (never P2 tuning); fixed Route-B CONFIRMED
unchanged.**

**Governance (2026-09-16):** permanent hierarchy — scientific truth =
this file; execution truth = `PROGRESS.md`; decisions (append-only) =
`DECISIONS.md`. Protocol: `docs/EXECUTION_AND_VALIDATION_PROTOCOL_V2.md`
(CURRENT PHASE = **Repository change localization / impact selection**).

**Phase:** paper submitted (ICCI shorthand; repo artifact = IEEE-format V20
submission) → **EVENING AUTONOMOUS MISSION (2026-09-16): Proposal V1.2
(supervisor-ready, 7 pages); BibTeX triage (13 exports, 10 high-priority
verified from primary sources) + 6 traceability ledgers; LocAgent P5R forensics
+ rescue pilot (0/5 usable → full rerun NOT triggered; P5 immutable); Route B
candidate-level omission recovery V1 — R4 Classical CIA beats Random at B=5 on
DEV_VALIDATION (0.180 vs 0.037; no universe-size artifact), the FIRST positive
candidate-level signal; Saleor Stage-2 READY-TO-RUN (full history 22,615
commits; frame 6000→2409→1352→1316; split proposal; gates); semantic-proxy
audit protocol + 25 DEVELOPMENT-only evidence packets; living-review novelty
update; NestJS readiness (TS universe semantics).**
Post-submission window. Scientific runs remaining in this block: ZERO (the
development-inference protocol has been executed).

**CURRENT TRUTH (2026-09-17, overnight + continuation missions):**
→ **ROUTE B V2 (candidate-level omission recovery) robustness closure COMPLETE
(2026-09-17; 174 development tasks; ZERO new model calls):** budget curve
B∈{0,1,3,5,10}; analytic hypergeometric Random control; Classical-CIA frozen
primary (0.5 BM25 + 0.5 graph neighbor hybrid predeclared secondary); 5/5 folds
positive; 4/4 B-points above Random; bootstrap CIs exclude zero at every B
(B=5 +0.136 [+0.092,+0.184]); no omitted/universe-size artifact (corr
−0.119/−0.117); **progression gate PASS** → verifier pilot authorized.
**Bounded verifier pilot EXECUTED (2026-09-17; 30 calls, 6,748 tokens, $0.0023;
30/30 valid; Oracle-in-top-B = 1.000; verifier ORR 0.86–1.00; dominant loss =
first-pass omission; diagnostic only).** History/co-change arm beats analytic
Random on 94 tasks with parent-visible history; CIA remains frozen primary.
**Saleor: production-only materializer portability fix + EQUIVALENCE 98/98 PASS
+ 150/150 DEVELOPMENT bundles built (2026-09-17; ZERO model calls; canonical
universe+graph hashes identical to pre-portability snapshot, 0 mismatch;
INTERNAL_TEST/RESERVE sealed).** **Saleor sparse inference FAIL-CLOSED on budget
(1/450 smoke cell, $0.0047; full run projects ~6.5–7.4M tokens / $2.13–2.23,
2.4–2.7× the authorized 2.7M/$1.00 ceiling) → Saleor Route-B replication
BLOCKED.** **djangoCMS Route-B confirmatory-freeze packet COMPLETE (ready-to-
approve; choice B = ranking + actual verifier; INTERNAL_TEST sealed).** **P2
adaptive budget CONDITIONAL (pre-registration note; no learned policy).**
**Semantic-proxy two-rater audit machine-prep FINISHED (integrity PASS, kappa
tests 7/7, synthetic dry-run NOT_REAL PASS, one-page checklist; human judgments
pending).** **Proposal V1.3 remains the print candidate (V1.4 NOT created — no
material claim change).**

**CURRENT TRUTH (2026-09-17, identity correction + clean Saleor run + transfer):**
→ **SALEOR IDENTITY/PROVENANCE CORRECTED (2026-09-17; ZERO model calls):**
case IDs migrated deterministically `djangocms-rc-<sha>` → `saleor-rc-<sha>`;
repository URL/anchor/license/repo identity corrected; old→new mapping
(`research/transparency/saleor_case_id_migration.json`); **150/150
scientific-payload equivalence PASS** (commits/split/universes/proxies/edges
identical to pre-migration snapshot); the pre-fix single smoke call is archived
as operational (NOT scientific evidence); stale Saleor docs/harness reconciled.
→ **SALEOR CLEAN 150×3 DEVELOPMENT SPARSE RUN EXECUTED (2026-09-17):** 450 cells
(150 tasks × 3 reps); **446 valid / 4 failed** (3× HTTP 429 transport on
`saleor-rc-012472eb8482` + 1× schema duplicate-id on `saleor-rc-d7fe298a4752`);
**7,316,986 tokens / $2.31** within the re-authorized hard ceilings
(450 cells / 9,000,000 tokens / $3.00); 150 independent tasks; 0 truncations;
provider DeepInfra (frozen route); no result-dependent reruns; no Saleor-specific
tuning; INTERNAL_TEST/RESERVE sealed.
→ **SALEOR ROUTE-B TRANSFER REPLICATION = REPLICATES (2026-09-17; ZERO new model
calls):** frozen Route-B V2 protocol applied to Saleor DEV Sparse predictions
(149 tasks; `012472eb8482` excluded — no succeeded rep); **Classical-CIA best
arm**, mean curve delta **+0.1915** vs analytic Random; B=5 CIA **0.237** vs
Random **0.006** (delta +0.231, CI [+0.180, +0.287]); 5/5 folds positive; 4/4
B-points above Random; no size artifact (−0.048). **The bounded-verification
signal transfers to a second, much larger repository (Saleor B=5 delta +0.231 >
djangoCMS +0.136).** Per-repository primary; no djangoCMS+Saleor pooling as the
headline. djangoCMS confirmatory INTERNAL_TEST remains sealed.

**CURRENT TRUTH (2026-09-17, PRE-CONFIRMATORY HARDENING V14 — ranker identity
audit + incremental ablation + freeze packet V2 + API budget freeze + Proposal
V1.4; ZERO API; INTERNAL_TEST/RESERVE sealed):**
→ **A. RANKER-IDENTITY AUDIT (2026-09-17; zero API; deterministic
recomputation):** the frozen Route-B V2 arm historically labelled
`Classical-CIA` is exactly **`normalized BM25 + binary graph-neighbor
indicator`** (no dependency propagation / association / importance weighting;
the genuinely classical CIA baseline `classical_cia_baseline_v1.py` is a
DIFFERENT script). **CIA and Hybrid are mathematically RANK-EQUIVALENT**
(Hybrid = 0.5 × CIA key; positive scalar multiple → identical total order),
verified at top-B identity on 174 djangoCMS + 149 Saleor DEVELOPMENT tasks:
**0 differing task-budget cells** at every B∈{1,3,5,10}, full-rank identical.
Hybrid is classified a **redundant alias/control, NOT an independent
baseline** (`reports/ROUTE_B_RANKER_IDENTITY_AUDIT.md` +
`research/transparency/route_b_ranker_identity_audit.json`). Historical
results unchanged; correction appended.
→ **B. INCREMENTAL-EVIDENCE ABLATION (2026-09-17; zero API; characterization,
no method change):** composite−BM25 paired task-level deltas are small with
bootstrap CIs including zero at most B on BOTH repositories (djangoCMS B=5
+0.003 [−0.015,+0.019]; Saleor B=5 +0.003 [−0.017,+0.024]); the replicated
cross-repo signal is **predominantly LEXICAL (BM25)**; the graph-neighbor
increment is small and largely non-significant (`reports/ROUTE_B_INCREMENTAL_EVIDENCE_ABLATION.md`
+ `research/transparency/route_b_incremental_ablation.json`). History arm
(djangoCMS 94 tasks) beats Random but remains an additional arm, not the
frozen primary; Saleor history UNAVAILABLE (no cache).
→ **C. CONFIRMATORY FREEZE PACKET V2** (`reports/DJANGOCMS_ROUTE_B_CONFIRMATORY_FREEZE_PACKET_V2.md`)
supersedes V1 (V1 immutable): truthful ranker name + formula; CIA/Hybrid
redundancy; Saleor transfer now AVAILABLE + REPLICATES on DEVELOPMENT; exact
first-pass repetition rule (first SUCCEEDED rep's write-set per task);
failed-rep/task treatment (excluded if no succeeded rep); verifier input/output
semantics; 1 verifier call per (task,B), independent across B, B=0 no call;
B∈{0,1,3,5,10}; primary endpoint ORR + secondary P/R/F1/FNR; analytic Random;
task-level bootstrap; failure semantics; no result-dependent reruns. Frozen
claim: **end-to-end Sparse → frozen omitted-candidate ranker → bounded verifier
on djangoCMS INTERNAL_TEST**.
→ **D. CONFIRMATORY API BUDGET FREEZE** (`reports/DJANGOCMS_CONFIRMATORY_API_BUDGET_FREEZE.md`):
80 djangoCMS INTERNAL_TEST tasks; Sparse-v2 3-rep first pass (240 cells);
verifier at B={1,3,5,10} (320 calls; B=0 none). Expected 560 calls / ~1,443,395
tokens / ~$0.50; conservative hard ceilings **2,100,000 tokens / $1.00**;
per-call reservation rule (sparse p99 7,877 tok / $0.00302; verifier 400 tok /
$0.00015) so cumulative budget cannot overshoot materially. DEVELOPMENT
distributions only; ZERO test peek.
→ **E. PROPOSAL V1.4** (`msc_proposal/MSC_PROPOSAL_V1_4.tex/.pdf`;
`PROPOSAL_V1_4_AUDIT.md`; changelog + claims matrix updated; V1.3 immutable):
justified by the material Saleor DEV transfer replication; conservative updates —
Saleor 450-cell DEV run (446 valid / 4 failed; 7,316,986 tokens / $2.31; 0
truncations), Saleor transfer REPLICATES (149 tasks; B=5 0.237 vs Random 0.006,
delta +0.231 CI [+0.180,+0.287]), DEVELOPMENT-transfer boundary explicit,
`Classical-CIA` terminology corrected, predominantly-lexical signal stated, no
graph novelty claim, adaptive B_t conditional, INTERNAL_TEST/RESERVE sealed and
said so. **V1.4 print addendum (2026-09-17, same day):** Experimental Design
table rebuilt with 8 compact `tabularx` columns (overlap fixed, zero overfull
hboxes); bibliography rendered in the PDF (Section 11, BibTeX `unsrt`, 21
verified entries, all in-text citations resolve); timeline replaced with the
**2026-11 → 2027-10** schedule (intended substantive completion 2027-07/08;
2027-09/10 = publication/revision/admin buffer). Compiles clean: **10 pages**,
SHA-256
`50957a2525f7430de47fd9306895d2b4c80b30c358d3cafe6798a0a27b0525b1`.
**V1.4 confirmatory + P2 timeline + cover update (2026-09-17):** fixed
Route-B CONFIRMED on djangoCMS INTERNAL_TEST incorporated (abstract,
preliminary evidence, cross-repo section); first five timeline months aligned
to the real P2 program; conservative academic title page
(`MSC_PROPOSAL_V1_4_TITLEPAGE.tex/.pdf`, no IEEE author blocks) + combined
print artifact `MSC_PROPOSAL_V1_4_PRINT.pdf` (11 pages). Body recompile:
**10 pages**, SHA-256
`07cb0588bbc3c0f92e99c3634a1c325d5b8a03a6f6af706c393dad8c7c35497c`.

**CURRENT TRUTH (2026-09-17, DJANGOCMS CONFIRMATORY RUN — AUTHORIZED, EXECUTED,
CONFIRMS; ZERO method change):**
→ **A. AUTHORIZED OPENING.** Ahmed explicitly authorized opening **only**
djangoCMS V2 INTERNAL_TEST (80 tasks) under the frozen V2 confirmatory protocol
and budget. djangoCMS RESERVE (59), Saleor INTERNAL_TEST and Saleor RESERVE
remain **SEALED** (verified 0 materialized). The 80 INTERNAL_TEST bundles were
materialized deterministically (ZERO API) from the pinned djangocms cache with
the SAME frozen `miner.build_case` builder used for the 150 DEV bundles
(`scripts/build_v2_internal_test_cases.py`,
`benchmark_data/real_commit_impact_v2/v2_internal_test_manifest.json`).
→ **B. EXECUTION (exact frozen V2 protocol).** Sparse-v2 first pass 3 reps/task
(240 cells; qwen/qwen3-coder @ deepinfra/turbo, temp 0, cap 16384, Graph OFF);
first SUCCEEDED rep → write set; frozen `BM25+Graph-Neighbor Composite`
(= normalized_BM25 + binary_graph_neighbor, historical label Classical-CIA);
verifier 1 call/(task,B) for B∈{1,3,5,10}, cap 512, independent across B, B=0
none; analytic Random control; primary ORR/FNRR; secondary P/R/F1/FNR.
→ **C. BUDGET CLOSURE.** **560 calls / 1,470,174 tokens / $0.505917** — all
within the frozen ceilings (560 / 2,100,000 / $1.00); 240/240 sparse succeeded,
320/320 verifier succeeded, 0 failures, 0 excluded tasks; no stop triggered.
Raw responses + SHA-256: **560/560 verified**
(`research/djangocms-confirmatory-route-b/confirmatory_raw_manifest.json`).
→ **D. RESULT (CONFIRMS).** Composite ranker ORR vs analytic Random:
B=1 0.0591 vs 0.0055 (Δ +0.0522, CI [0.0163,0.0957]); B=3 0.1098 vs 0.0166
(Δ +0.0918, CI [0.043,0.1455]); B=5 0.165 vs 0.0277 (Δ +0.1367, CI
[0.0746,0.2046]); B=10 0.2669 vs 0.0554 (Δ +0.2108, CI [0.1376,0.2877]).
Gate PASS (5/5 folds positive; 4/4 B-points above Random; CIs exclude zero at
every B; no size artifact: corr −0.0368/−0.0332). Final selected set @ B=5:
P 0.2058 / R 0.284 / F1 0.2387 / FNR 0.716. **Classification: CONFIRMS.**
End-to-end verifier: B=5 ORR 0.1007 (Δ +0.0734, CI [0.0229,0.1308]); B≥3 CIs
exclude zero; B=1 CI touches zero (documented, not the primary claim).
→ **E. FROZEN BOUNDARIES.** The opened djangoCMS INTERNAL_TEST is now
**permanently used** as the confirmatory test and will **never** be reused as a
fresh test for future P2 algorithm selection. P2/adaptive work is evaluated on
DEVELOPMENT only (djangoCMS DEV + Saleor DEV). **No method/ranker/verifier
change was made based on outcomes.**
Evidence: `reports/DJANGOCMS_ROUTE_B_CONFIRMATORY_RESULT.md`,
`reports/DJANGOCMS_CONFIRMATORY_AUDIT.md`,
`research/djangocms-confirmatory-route-b/confirmatory_metrics.json`.

**CURRENT TRUTH (2026-09-17, PROPOSAL V1.5 POLISH + MATRIX + ABSTRACT +
SLIDE HANDOFF — docs-only milestone; ZERO API; no scientific input change;
V1.4 immutable):**
→ **V1.5 CREATED** (`msc_proposal/MSC_PROPOSAL_V1_5.tex/.pdf`; V1.4 remains
byte-identical, SHA-256 `07cb0588…`): (1) **abstract rewritten** to the
doctor-guide order (problem/context → limitation → precise gap → proposed
approach → experimental setting → strongest result only → confirmatory status
→ one scope limitation); "for the first time" and unscoped "robust" removed;
secondary details demoted to Preliminary Evidence (`ABSTRACT_REWRITE_NOTE.md`);
(2) **related-work comparison matrix ADDED** (Section 5, two compact
`tabularx` tables — design/structure + evidence/position; rows: Classical/
history CIA, Agentless, CodePlan, RepoCoder, LocAgent, GraphLocator, RepoGraph,
This proposal) — fixes the Section 4 forward-reference without deleting it; new
verified reference `repograph2025` (ICLR 2025, arXiv:2410.14684, verified from
the arXiv API); `references.bib` now 22 entries, 22/22 cited, no uncited dump;
(3) **terminology/claim-safety pass**: "Classical-CIA" → `BM25+Graph-Neighbor
Composite (historical label: Classical-CIA)` / `BM25+GraphNeighbor`; "fair
comparison" → `shared-protocol, budget-matched comparison`; "missed impacted
files" → `missed files in the observed historical change-set proxy`; ranking ≠
verification ≠ final localization made explicit; (4) **P2 stated as NOT
complete** — development research program (Nov 2026–Mar 2027), not a proven
contribution, with competitor/analogue families named (selective prediction,
cascades, optimal stopping, budgeted retrieval, value-of-information,
interpretable adaptive stopping); (5) **NestJS/NextJS = future external-validity
work only** (April 2027, conditional on the suitability gate AND
TypeScript-extractor readiness). Compile: **12 pages**, zero overfull, zero
underfull, zero undefined citations, zero BibTeX warnings; PDF SHA-256
`67dff046347847e1f80e01bdf313acf3cf2a577bfa2783f02686c4e3cf041ef7`.
→ **SLIDE HANDOFF PACKAGE CREATED** (`slides/HANDOFF_INTERACTIVE_MSC_SEMINAR_SLIDES.md`):
one-minute story, 20-slide interactive outline (18–24 range), toy 10-file
example, definitions (Sparse, Route B, B, Random, BM25, Composite, Oracle,
Verifier), frozen key numbers (Saleor 450/446/$2.31; Saleor B=5 0.237 vs 0.006;
djangoCMS confirmatory 560 calls/1.47M tokens/$0.506; confirmatory B=5 0.165 vs
0.0277; verifier B=5 ORR 0.1007; final set @B=5 P0.206/R0.284/F1 0.239/FNR
0.716), claim boundaries, Q&A — sufficient for a fresh LLM to build the deck
without reading the repo.
→ **P2 DOCS ALIGNED** (roadmap/evaluation-contract/pre-registration-note):
P2 NOT complete; fixed Route B CONFIRMED; P2 = development research program;
April 2027 NestJS/NextJS external-validity conditional on suitability gate +
TS extractor; pre-registration gate 1 now satisfied (confirmatory CONFIRMED),
gate 2 (approved adaptive protocol) still pending.
→ **BOUNDARY HELD:** ZERO API; no method/ranker/verifier change; djangoCMS
RESERVE + Saleor INTERNAL_TEST/RESERVE still sealed; the opened djangoCMS
INTERNAL_TEST permanently spent (never reused as a fresh P2 test); no stable
tag moved.

---

## 1. Submitted science — FROZEN (do not touch, do not rerun)

- Manuscript: `paper/v20-final/` (blind + supervisor TEX/PDF, `v20_body.tex`,
  `references.bib`, change log, claims matrix 43/43, reviewer-risk audit).
- Submission ZIP: `paper/v20-final/V20_FINAL_SUBMISSION.zip`
  SHA-256 `9CB5BDCCFCE8542E5A936136B60E01471FB917EF18B5B537220966421425E138`
  (10 entries, sidecar verified).
- Science candidate commit `42755df0cb53a60be1c8a2a3c3322d34ef3d8155`;
  submission archive commit `0a5928ce615340262ca3697615eee55fb8847ed6`;
  corrected main base `884ba7982f283b2e78c48d768d34f2f5a726a862`.
- Conference paper/submission ID and submission timestamp: **NOT recorded in
  the repo** (truthful: nothing to report; never fabricated).
- Full per-file hashes: `paper/v20-final/ICCI_SUBMISSION_RECORD_2026-09-15.json`.

## 2. Completed evidence (all audited / frozen)

| Study | Status | Where |
|---|---|---|
| Selection-stage benchmark (Todo + djangoCMS, 60-cell Stage-C) | CLOSED / AUDITED | `reports/`, tag `v0.11.0-benchmark-complete` |
| ImpactPlan-v2 post-hoc/exploratory (30 cells) | COMPLETE / AUDITED | `reports/scientific-stagec-djangocms-impactplan-v2-01/` |
| M1A controlled 4096-cap feasibility boundary | COMPLETE / AUDITED | `reports/CONTROLLED_ENCODING_4096_FEASIBILITY_RESULT.md` |
| M1B controlled 16K cap-relaxed ablation | COMPLETE / AUDITED | `reports/CONTROLLED_ENCODING_16K_RESULT.md` |
| M1 defensive closure (threat matrix, n=6 scenario stats) | COMPLETE | `reports/M1_*` |
| M3 graph ablation C0/C1/C2 (90 cells, development-set) | COMPLETE / AUDITED | `reports/M3_GRAPH_*`; hints MIXED, gated disclosure NOT PROMISING |
| M4A-1 RealCommitImpactDataset-v1 miner + 6 MINER_DEV | COMPLETE / AUDITED | `reports/REAL_COMMIT_M4A1_*`; ZERO API |
| M4A-2 scientific corpus (40 cases) + split freeze | COMPLETE / AUDITED | `reports/REAL_COMMIT_M4A2_*`; ZERO API |
| M4A-3/P1 real held-out evaluation (60/60 cells) | EXECUTED (2026-09-14) | `research/real-commit-p1-01/`, `reports/REAL_COMMIT_M4A3_P1_*` |
| P5 LocAgent shared-protocol comparison (P5-A/B/C) | COMPLETE (2026-09-15) + C1–C7 reporting corrections | `reports/LOCAGENT_P5C_*`, `research/locagent-p5b/` |

## 3. Exact tags / SHAs (authoritative)

- `v0.11.0-benchmark-complete` — benchmark closed + audited (NOT end-to-end
  executor success).
- `v0.11.1-p1-serialization-docs-model-refactor`, `v0.11.2-p5-locagent-shared-comparison`,
  `v0.11.3-p5-reporting-corrections` @ `884ba79…`.
- `cheap-baselines-v1-dev-2026-09-16` — Protocol A cheap non-LLM baselines v1
  DEV evidence tag @ commit `541c8ba…` (tag object `4b96049…`; audited
  DEVELOPMENT evidence, NOT confirmatory; NOT a stable-tag move).
- `research-harness-v1-dev-2026-09-16` — pluggable research harness V1 + living
  systematic review V1 DEV evidence tag (audited DEVELOPMENT/architecture
  evidence; NOT a stable-tag move).
- `omission-risk-feature-study-v1-dev-2026-09-16` — Omission-Risk Feature Study
  V1 (deterministic-first-pass development analysis + Phase-B preflight +
  audit) DEV evidence tag (audited DEVELOPMENT evidence; NOT a stable-tag
  move).
- Study tags: `real-commit-p1-full-v2-vs-sparse-v2-01-audited`,
  `real-commit-impact-dataset-v1-corpus-audited`,
  `real-commit-impact-dataset-v1-m4a1-closure-audited`,
  `graph-c0-c1-c2-01-study-01-audited`,
  `controlled-encoding-ablation-16k-study-01-audited`, etc.
- P1 frozen protocol `real-commit-p1-v1.0.0`; P1 model `qwen/qwen3-coder`
  (Qwen3-Coder-480B-A35B-Instruct) @ `deepinfra/turbo`; temp 0; cap 16384; Graph OFF.
- LocAgent pinned upstream commit `4935b557326c154bad8e8dcf3747cc8d32d1f387`.

## 4. Datasets / splits (frozen, ZERO-API)

- `benchmark_data/real_commit_impact_v1/`: **40 scientific djangoCMS cases** +
  6 MINER_DEV cases.
- Split freeze (seed `20260913`, metadata-only, pre-model): **TRAIN 24 /
  VALIDATION 6 / HELD_OUT_TEST 10** (`split_freeze.json`,
  `scientific_manifest.json`).
- Gold = **OBSERVED CHANGE-SET PROXY** (evaluation-only), never semantic
  ground truth.

## 5. Exposed test sets — PERMANENT (do not tune)

- **The 10 HELD_OUT_TEST tasks are PERMANENTLY EXPOSED** (P1 M4A-3/P1 ran
  Full-v2 and Sparse-v2 with 3 nested reps; P5-C ran LocAgent 10/10). They are
  used for reporting/audit only.
- **DO NOT TUNE any new method on these 10 tasks.** Any tuned-threshold /
  selected-feature / escalation-policy decision must be made on
  TRAIN/VALIDATION (or MINER_DEV) and confirmed on a FRESH held-out split
  that has never been used for any selection decision.
- **DO NOT CALL-CONFIRMATORY on the exposed 10** to "check" a new method:
  repeated confirmatory inference on the same exposed split is confirmatory
  bias. Fresh confirmatory protocol = new repository OR new non-exposed split.

## 6. Current threats (active, from `reports/M1_THREATS_TO_VALIDITY_MATRIX.md`)

1. HELD_OUT_TEST exposure (now permanent — mitigation: fresh split required).
2. Survivor-conditioned LocAgent metrics must never be reported as headline.
3. Change-set proxy is an observed diff, not semantic ground truth.
4. Single-repository, single-model selection evidence (djangoCMS;
   Qwen3-Coder-480B-A35B-Instruct).
5. LocAgent provider route is OpenRouter-routed (backend not pinned per call);
   cost $9.9288 is a NORMALIZED estimate, not provider-billed.
6. No arm-superiority claim from P1: paired ΔF1 CIs cross zero.
7. Selective escalation is NOT validated — proposal only.

## 7. Current numbers (frozen, recomputed 2026-09-15, ZERO API)

### P1 (10 tasks × 2 arms × 3 reps = 60 cells; 60/60 valid; 566,755 tokens; $0.36)
- Full-v2 micro: P 0.3388 / R 0.3694 / F1 0.3534 / FNR 0.6306.
- Sparse-v2 micro: P 0.3867 / R 0.2613 / F1 0.3118 / FNR 0.7387.
- Paired bootstrap over 10 tasks: ΔF1 −0.0088 [−0.1297, +0.1189] (crosses zero);
  Δcost −$0.0235 [−0.0244, −0.0228] (cost effect supported, descriptive).

### Cheapest-baseline block (Protocol A, 2026-09-16, ZERO API, DEVELOPMENT evidence — CLOSED + DEV tag)
- B0 Random@K ≈ floor (pooled F1 0.012–0.021 across K).
- B1 BM25@K strongest cheap lexical: **VALIDATION is the primary
  development-decision table** — BM25@3 P 0.333/R 0.240/F1 **0.279** (precision
  operating point); BM25@10 P 0.217/R 0.520/F1 **0.306**/FNR 0.480 (recall
  operating point, highest VALIDATION F1). **K is an operating-point curve, NOT
  a final configuration.**
- B2 path_token@K / B3 Graph@K ≈ 0.18–0.19 pooled F1 @K=3 (graph ≈ path_token;
  Graph@K seeds are lexical/path-token-derived → this shows the cheap
  lexical-seeded expansion adds little over the seed signal, NOT that graph
  reasoning is generally unhelpful).
- B4 Hybrid@K ≈ BM25@K (pooled F1 0.258 @K=3; frozen 0.5/0.5 fusion does not
  materially improve over BM25 → motivates bounded/selective graph verification,
  not score fusion).
- **Fair-comparison caveat (safe wording):** BM25 provides a meaningful
  zero-LLM localization signal on development data; whether it matches or
  underperforms the LLM planners remains untested under a shared fresh
  confirmatory protocol. Full-v2 F1 0.353 / Sparse-v2 F1 0.312 (exposed
  HELD_OUT) are directional context only, never a head-to-head ranking.
- Efficiency: BM25 wall ≈ 403 s dominated by parent git-archive
  materialization (snapshot/index-build cost), queries ~1.3 s total (not
  "403-second inference"); path_token/graph < 2 s; **0 LLM calls, 0 tokens**.
- **Path-mention sensitivity (ZERO API, diagnostic):** excluding the 3 TRAIN
  cases whose full intent mentions a changed path, path-clean BM25@3 F1
  0.283 → 0.262 (TRAIN) and 0.282 → 0.267 (pooled); material qualitative
  ordering unchanged. `research/cheap-baselines-v1/path_mention_sensitivity_v1.json`.
- Artifacts: `research/cheap-baselines-v1/`; six gates + audit PASS
  (`reports/CHEAP_BASELINES_V1_REPORT.md`, `_AUDIT.md`); merged to `main`;
  tag `cheap-baselines-v1-dev-2026-09-16` = audited DEVELOPMENT evidence,
  NOT confirmatory.

### P5 LocAgent (10 tasks × 1 exec; 402 calls; 32.8M tokens; $9.9288 est.)
- **Headline (A, fail-closed all-10):** TP 10 / FP 13 / FN 27 → P 0.4348 /
  R 0.2703 / F1 0.3333 / FNR 0.7297.
- **Diagnostic (B, usable-5, survivor-conditioned — NOT headline):** micro
  P 0.4348 / R 0.4000 / F1 0.4167 / FNR 0.6000; macro P 0.6909 / R 0.6033 /
  F1 0.6370 / FNR 0.3967.
- Failure taxonomy: **2 timeout / 1 context-length BadRequest / 2
  completed-but-empty** (NOT "5 timeouts").
- Official native Acc@K: Acc@1 4/10, Acc@3 4/10, Acc@5 2/10 (the old 8/10,
  9/10 were item-hit sums — corrected).
- Source: `research/locagent-p5b/locagent_two_way.json` +
  `reports/LOCAGENT_P5C_SHARED_COMPARISON.md`.

### Four-action FN breakdown (existing P1 raw outputs; secondary diagnostic)
- Full-v2 FN 70: PRESERVE 70 / VALIDATE 0 / HUMAN_REVIEW 0.
- Sparse-v2 FN 82: PRESERVE 74 / VALIDATE 8 / HUMAN_REVIEW 0.
- Both arms: PRESERVE 144 / VALIDATE 8 / HUMAN_REVIEW 0 (REGENERATE excluded
  by construction). See
  `research/post-icci-zero-api-closure/four_action_fn_breakdown.{json,csv}`.

### Harness V1 + living systematic review V1 (2026-09-16; T3 architecture; ZERO API — CLOSED + DEV tag)
- Reusable experiment harness `src/benchmark/harness/` with seams:
  DatasetAdapter, SnapshotProvider/RepositoryView, Ranker, Planner,
  ModelBackend, RiskScorer (interface only), Verifier (interface only),
  BudgetPolicy, common Evaluator, versioned ExperimentSpec. Config-driven name
  registry; django rules in a django adapter; future Saleor rules in a
  fail-closed Saleor adapter; model/provider names are config; budget explicit
  and persisted.
- **Protocol-A compatibility layer reproduces the frozen cheap-baseline outputs
  byte-for-byte**: full equivalence run 30 cases × 5 methods × 4 K = 600 rows
  scientific projection + per_task + aggregates identical to
  `research/cheap-baselines-v1/*.json`
  (evidence `research/harness-protocol-a-equivalence/raw_predictions_via_harness_v1.json`).
- Living review: `docs/LIVING_SYSTEMATIC_REVIEW.md`,
  `research/literature/review_matrix.csv` (12 seeded systems; only LocAgent
  VERIFIED with direct evidence; all others SEEDED — verify primary source),
  `research/literature/search_log.csv`, `research/literature/idea_ledger.md`
  (ideas I1–I7 with TEST/WATCH/BOUNDARY dispositions).
- Validation: six T3 gates + independent audit PASS
  (`reports/RESEARCH_HARNESS_V1_REPORT.md`, `_AUDIT.md`,
  `reports/research_harness_v1_gates.json`); 44 new tests; full suite 3270
  passed / 33 skipped / 2 pre-existing environmental failures (missing pinned
  djangocms repo checkout; identical on clean base).
- **ONE next scientific step: OMISSION_RISK_FEATURE_STUDY_V1 (TRAIN/VALIDATION
  only). NOT STARTED here.**

### Omission-Risk Feature Study V1 (2026-09-16; T3; ZERO new LLM/API calls — deterministic-first-pass DEVELOPMENT ANALYSIS COMPLETE + AUDITED; registered Sparse-v2-label study DEFERRED)
- **Phase-B preflight A–G COMPLETE** (`reports/OMISSION_RISK_REPOSITORY_EVIDENCE_AUDIT.md`
  + JSON/CSV): Gate A = TRAIN/VALIDATION have **NO Sparse-v2 predictions** (P1
  ran only on HELD_OUT_TEST); Gate B = single repository (djangoCMS), graph
  present on all 30 tasks (524–564 edges, 0 zero-edge), history_available NO,
  parent-commit BM25 corpus NOT re-materializable (missing pinned git cache);
  Gate G = 10-row manual equivalence sanity sample 10/10 prediction+metric
  equal.
- **Deterministic-first-pass development analysis** (metadata-corpus BM25@K
  first pass, 83 features in families A/B/C/E/F, n=30): label prevalence 73–80%
  across K∈{3,5,10}; random AUROC band radius ~0.24–0.26; **only 1–2 of 83
  features exceed the random 95% band (fewer than the ~12 expected by chance),
  all anti-correlated with the pre-registered direction** (peaked/confident
  BM25 → more omissions). Adaptive-K does not beat fixed K=10. Cost analysis:
  always-escalate dominates at every C_FN/C_VERIFY ratio because the first pass
  omits files on ~73–80% of tasks. No feature frozen for RiskScorer v1.
- **Registered Sparse-v2-label study DEFERRED** (amendment): producing it
  requires a new scientific LLM run → frozen **DEVELOPMENT-INFERENCE protocol**
  (`docs/OMISSION_RISK_DEVELOPMENT_INFERENCE_PROTOCOL.md`; 90-cell Sparse-v2 on
  TRAIN/VALIDATION, ~497.6k tokens, ~$0.19, budget ceiling $0.30) gated on
  **Ahmed's approval** — no LLM call without it.
- **Registered Sparse-v2-label study EXECUTED 2026-09-16 (approved 90-cell
  development-inference, TRAIN/VALIDATION only):** 90/90 valid, 490,747 tokens /
  $0.184 (within the 600,000-token AND $0.30 hard stop); task-level Sparse-v2
  `has_fn` prevalence **86.7% (26/30, 4 negatives)**; **class-balance gate
  FAILED → no multivariable RiskScorer; descriptive/single-feature only**; only
  **3/97 features above the random band** (4.85 expected by chance — a
  retrieval-peakiness cluster, now direction-consistent); Sparse–BM25
  disagreement anti-predictive (0.303); graph inside band; adaptive-K no help;
  always-escalate still dominates; **RiskScorer v1 NOT statistically justified**.
  Report `reports/OMISSION_RISK_SPARSE_V2_INFERENCE_REPORT.md`; audit
  `reports/OMISSION_RISK_INFERENCE_AUDIT.md` (31/31 PASS). Run evidence in
  `research/omission-risk-feature-study-v1/sparse_v2_trainval_*` + raw sha256
  sidecars; analysis in `research/omission-risk-feature-study-v1/sparse_v2_label_analysis/`.
- Artifacts: `research/omission-risk-feature-study-v1/` (feature_table.csv,
  feature_manifest.json, single_feature_results.json, adaptive_k_results.json,
  cost_sensitive_analysis.json, raw_task_level_inputs.json, data_availability.json,
  repository_evidence_audit.{json,csv}, equivalence_sanity_sample.json,
  feature_table_with_flags.csv); reports
  `reports/OMISSION_RISK_FEATURE_STUDY_V1_REPORT.md`, `_AUDIT.md`,
  `reports/omission_risk_feature_study_v1_gates.json`; 19 new unit tests; six
  gates + independent audit PASS.
- Living review updated (V1.1 verification pass; Shichao Zhang adaptive-computation
  line VERIFIED; priority rows verified/corrected — Agentless, CodePlan,
  RepoCoder, AutoCodeRover, RepoGraph, GraphLocator, RPG/ZeroRepo).

## 8. Next experiment — ONLY ONE (not started, not authorized without review)

**Protocol A (cheap non-LLM baselines v1) is COMPLETE AND CLOSED (2026-09-16;
TRAIN 24 + VALIDATION 6; ZERO API; six gates + audit PASS; merged to main; DEV
tag `cheap-baselines-v1-dev-2026-09-16`).**

**PLUGGABLE RESEARCH HARNESS V1 + LIVING SYSTEMATIC REVIEW V1 are COMPLETE AND
AUDITED (2026-09-16; T3 reusable experiment architecture; ZERO API; six T3
gates + audit PASS; Protocol-A outputs reproduced byte-for-byte through the
compatibility layer — 30 cases × 5 methods × 4 K = 600 rows + aggregates;
merged to main; DEV tag `research-harness-v1-dev-2026-09-16`).**

**OMISSION-RISK FEATURE STUDY V1 is COMPLETE AS A DETERMINISTIC-FIRST-PASS
DEVELOPMENT ANALYSIS (2026-09-16; T3; ZERO new LLM/API calls; Phase-B preflight
A–G + six gates + independent audit PASS; merged to main; DEV tag
`omission-risk-feature-study-v1-dev-2026-09-16`). The registered Sparse-v2-label
study is DEFERRED (TRAIN/VALIDATION have no Sparse-v2 predictions).**
**REGISTERED SPARSE-v2-LABEL STUDY EXECUTED (2026-09-16) via the APPROVED
DEVELOPMENT-INFERENCE protocol** (`docs/OMISSION_RISK_DEVELOPMENT_INFERENCE_PROTOCOL.md`):
90-cell Sparse-v2 run on TRAIN/VALIDATION complete — 90/90 valid, 490,747 tokens
/ $0.184 (within the 600,000-token AND $0.30 hard stop); Sparse-v2 `has_fn`
prevalence 86.7% (26/30, 4 negatives); class-balance gate FAILED → descriptive/
single-feature only, NO multivariable RiskScorer; no reliable risk signal
survives the random band; report `reports/OMISSION_RISK_SPARSE_V2_INFERENCE_REPORT.md`;
audit PASS. Saleor remains the second-repository confirmatory line,
DOCUMENT-ONLY for now (`docs/SALEOR_CONFIRMATORY_PROTOCOL_DRAFT.md`).

Sequence per the MSc roadmap:
`Sparse first pass → omission-risk detection → selective graph-guided escalation
→ bounded false-negative verification`.

Do NOT automatically begin: Saleor scientific execution, risk-detector
training, selective escalation, faithful LocAgent inference, new LLM calls, or
new model-family runs.

## 9. DO-NOT warnings (operational)

- **DO-NOT-TUNE** on the exposed HELD_OUT_TEST ten.
- **DO-NOT-CALL-CONFIRMATORY** on the exposed ten.
- **DO-NOT** claim selective escalation has been validated.
- **DO-NOT** run Saleor / LocBench / new LocAgent inference / new model
  matrices without a fresh preregistration + frozen budget.
- **DO-NOT** alter frozen P1/P5 outputs; all post-ICCI analyses are
  read-only recomputations from existing evidence.
- **DO-NOT** run any new scientific LLM/API call (including the deferred
  Sparse-v2 development inference) without Ahmed's approval of
  `docs/OMISSION_RISK_DEVELOPMENT_INFERENCE_PROTOCOL.md`.