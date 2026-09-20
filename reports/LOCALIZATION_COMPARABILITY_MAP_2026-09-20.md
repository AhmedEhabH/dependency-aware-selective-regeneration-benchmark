# LOCALIZATION COMPARABILITY MAP (2026-09-20)

**Mission:** ISSUE_GROUNDED_INTENT_HEADROOM (T3)
**Companion report:** `ISSUE_GROUNDED_INTENT_HEADROOM_2026-09-20.md`
**Authoring agent:** openrouter/deepseek/deepseek-v4-flash-0731

Purpose: a short, human-readable map of how this benchmark, Ying et al. 2004,
ROSE / Zimmermann et al. 2004, LocAgent, RepoMem, MULocBench, and (where
appropriate) Agentless relate to each other, and WHY headline numbers cannot be
compared directly with our exact changed-file-set F1.

---

## 1. Comparator table

| Method | Textual input | Already-changed-file seed known? | Repository access | Output type | Metric | Reported headline number | Directly comparable to our set-F1? |
|---|---|---|---|---|---|---|---|
| **This benchmark (djangoCMS / Saleor DEV)** | GitHub commit message (intent proxy) | NO (no known target-file seed) | Full repository snapshot + dependency graph | Predicted affected-file SET | Exact set Precision / Recall / F1 over proxy-changed files | Sparse F1 0.318 / 0.261; V1 0.334/0.336; V2 0.345/0.348 | (reference) |
| **Ying et al. 2004** (change history) | Historical change data; past change records | YES (an initial change is the seed) | Repository change history | Ranked candidate files | Recall at top-N of suggested fixes | ~e.g. top-ranked suggestions evaluated by recall | NO - seeded, historical, not issue/commit-text driven |
| **ROSE / Zimmermann et al. 2004** | An initial change (which file changed) | YES (RATING starts from an already-changed entity) | Repository change history | Association-rule predictions of further files / functions / variables | Recall / likelihood (top-3 suggestions) | ~26% of further FILES, ~15% of functions/variables predicted, top-3 likelihood ~64% (official project summary) | NO - requires an already-changed entity seed |
| **LocAgent** (RepoGraph-ESA, Acc@k) | Issue description | NO (issue-driven) | Code repository | Top-K file (or issue) suggestions | Accuracy@K | F1~0.333 reported on a 10-task exposed population (NOT our 323-task DEV population) | NOT DIRECTLY - different task population / evaluator; exact matched comparison requires a separate matched protocol |
| **RepoMem** | Issue description | NO | Repository + memory | Ranked files | F1 / recall across issue benchmarks | varies by dataset | PARTIAL - same general output type, but benchmark/evaluator differ |
| **MULocBench methods** | Issue description | NO | Multi-language repos | Ranked files | Accuracy@K / F1 | varies by repo/method | PARTIAL - multi-language scripts; different repositories and ground truth |
| **Agentless** (localization stage) | Issue description | NO | Source repo | Ranked suspicious files | Localization Top-k | LOW Top-k hit rates (reported) | PARTIAL - same general task, different bench items / ground truth |

---

## 2. Three categories

### A. CHANGE-HISTORY WITH KNOWN SEED
- **ROSE / Zimmermann et al. 2004**
- **Ying et al. 2004**

These methods start from an already-known changed entity (a file or a change)
and predict further files via co-change / association rules. They do NOT solve
"which files change given only a textual intent" - the seed is given.

### B. ISSUE-DRIVEN FILE LOCALIZATION
- **Agentless**
- **LocAgent**
- **RepoMem**
- **MULocBench methods**

These take an issue description and rank repository files. They are the
closest competitors in task shape, but their benchmark items, repositories,
ground-truth definitions, and evaluation conventions differ from ours.

### C. OUR CURRENT SETTING
- Short commit-message intent proxy
- No known target-file seed
- Exact predicted file-SET Precision / Recall / F1 against the proxy-changed
  set

---

## 3. Why headline Acc@K values cannot be compared directly with set-F1

1. **Different output semantics.** Accuracy@K normally counts whether the
   top-K list CONTAINS a target file (a retrieval framing). Set-F1 scores the
   whole predicted set against the whole observed changed set - a binary-class
   framing. A method can have high Acc@1 while producing many false positives
   and therefore a low F1; a method can have modest Acc@k but a high F1 if its
   predicted set closely matches the observed set.
2. **Different task populations.** LocAgent's F1 ~0.333 came from a DIFFERENT
   exposed 10-task population, not our 323-task DEVELOPMENT population; the
   ROSE/Ying headline numbers come from other repositories and eras.
3. **Different ground truth and proxy.** We use the observed change-set as an
   evaluation proxy and exclude generated/vendor/test files by policy; other
   works use their own gold labels and file policies.
4. **Different input.** We explicitly withhold the target-file seed; the change
   -history methods (category A) receive it.

Because of 1-4, a cross-method "winner/loser" ranking across incompatible
metrics is scientifically unsound and is NOT made here.

---

## 4. Explicit corrections (frozen prior claims)

- **ROSE**: the official project text states that, after an initial change,
  ROSE correctly predicted about **26% of further files** and about **15% of
  functions/variables**, with a correct location in the top three suggestions
  with likelihood about **64%**. It is NOT claimed that 26% is precision and
  15% is recall unless the original paper explicitly supports that mapping.
  ROSE has an already-changed entity as input and is not directly comparable.
- **KG-Commit**: if mentioned anywhere, it must be labeled JIT DEFECT
  PREDICTION, not file localization.
- No claim is made that "our F1 is higher than the literature".
  Allowed wording: **"No directly comparable apples-to-apples benchmark has
  yet been identified for exact changed-file-set F1 from short commit-message
  intent without an already-known changed-file seed."**
- No claim that "F1 >= 0.8 is impossible".

---

## 5. Conclusion (key message)

The current benchmark occupies a distinct cell of the design space: exact
file-set P/R/F1 from a short textual intent with the target-file seed withheld.
Headline Acc@K / F1 numbers from the literature belong to different task
framings, populations, and evaluation conventions, so they are NOT directly
comparable cross-method.