# FN ADD-Queue Progression Gate

**Date:** 2026-09-18  **Tier:** T3 (ZERO API)  **Reference budget:** B=5

A queue advances to a bounded LLM-verifier experiment ONLY if all seven conditions hold on BOTH repos.

| Queue | djangocms ΔORR | saleor ΔORR | dc folds+ | sc folds+ | dc naiveF1 | sc naiveF1 | dc oracleRevF1 | sc oracleRevF1 | gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25+ReverseDependency | -0.011 | +0.001 | 3/5 | 4/5 | 0.227 | 0.239 | 0.442 | 0.428 | FAIL |
| BM25+ProviderConsumerSupport | -0.025 | -0.001 | 3/5 | 4/5 | 0.220 | 0.239 | 0.431 | 0.428 | FAIL |
| BM25+ComplementaryUnion | -0.086 | -0.209 | 1/5 | 0/5 | 0.188 | 0.141 | 0.381 | 0.276 | FAIL |

**Decision: RECALL_SIGNAL_HEADROOM_ONLY**

## Rationale

- Sections 4-5 established that FN candidate availability is NOT the binding constraint: the reverse-1hop
  consumer pool alone carries 55.8% (djangoCMS) / 72.4% (Saleor) of all FNs at K=5 oracle ceiling, and the
  full complementary union carries 72.5% / 87.0%.
- But NO simple deterministic ADD queue (BM25 + binary structural flags) beats the frozen Route-B composite at
  matched budget on ORR, and none shows material FN recovery above Route-B.
- Oracle-reviewer simulation shows meaningful headroom (final F1 up to 0.44-0.50 at B=5 under a perfect
  reviewer vs naive union 0.19-0.24), confirming the loss is RANKING + VERIFIER-ACCEPTANCE, not candidate
  availability or the queue concept itself.
- Therefore no bounded LLM-verifier experiment is authorized by THIS mission.