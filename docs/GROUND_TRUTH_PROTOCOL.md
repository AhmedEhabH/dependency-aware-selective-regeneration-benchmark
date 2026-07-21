# Ground Truth Protocol — v1.0 (FROZEN)

**Part of:** Research Protocol v1.0
**Approval Date:** 2026-07-22

---

## 1. Ground-Truth Dimensions

Each candidate artifact receives one of four action labels:

| Action | Definition |
|--------|-----------|
| **Regenerate** | Artifact content must change to satisfy the new requirement |
| **Preserve** | Artifact must remain unchanged |
| **Validate only** | No edit expected, but execution or conformance checking is required |
| **Human review** | Insufficient confidence for automated decision |

## 2. Sources

Ground truth is constructed from:
1. Repository history — actual changes in analogous past commits
2. Static analysis — dependency graphs, call graphs, data-flow analysis
3. Test coverage — which tests exercise which artifacts
4. Architecture documentation — ADRs, module boundaries
5. Independent expert annotation — at least two annotators per scenario

## 3. Candidate Artifact Universe (per AC-01)

The candidate universe is frozen per repository and scenario before any strategy execution. It includes:
- Tracked source files (Python, Django-specific files)
- Relevant tests (unit, integration, functional)
- Migrations
- API/schema definitions
- Documentation (inline, external, README)
- Configuration files
- Architecture artifacts

### Exclusions (documented per repository)
- Vendored dependencies
- Generated files, binaries, caches
- Build outputs
- VCS internals (.git)
- Unrelated generated translations

True-negative and false-positive rates are reported only when the candidate artifact universe is complete and frozen.

## 4. Annotation Process

### 4.1 Annotators (per DA-06)
Minimum: researcher/author + one independent Python/Django-capable software engineer or researcher + supervisor or third qualified reviewer for adjudication. The independent annotator must have at least one year of practical or research software-development experience and complete a pilot annotation exercise.

### 4.2 Materials per Annotator
- Repository snapshot (commit SHA)
- Requirement change description (before/after)
- Acceptance criteria
- List of candidate artifacts with types
- Annotation guidelines defining each action
- Example annotations from a pilot scenario (not in main study)

### 4.3 Independence
Annotators work independently without discussion. Annotations submitted through a structured form (YAML or CSV template). No access to each other's annotations until adjudication.

### 4.4 Pilot Annotation
One pilot scenario per repository used for annotator training. Pilot results not included in final ground truth. Annotator feedback used to refine guidelines.

## 5. Inter-Annotator Agreement (per DA-04)

| Agreement Level | Interpretation |
|----------------|---------------|
| κ ≥ 0.80 | Strong |
| 0.70 ≤ κ < 0.80 | Acceptable with adjudication |
| κ < 0.70 | Refine guide, recalibrate, re-annotate |

Report pre-adjudication agreement: overall, per repository, and per action class.

Use Cohen's kappa or weighted kappa for two annotators. Krippendorff's alpha may be used for more annotators or missing labels.

## 6. Adjudication Process (per DA-05)

1. Two independent annotations completed.
2. Disagreements resolved through documented adjudication discussion.
3. If unresolved, a third qualified adjudicator reviews.
4. `human_review` assigned only when evidence remains genuinely insufficient.

All original labels and rationales are retained.

## 7. Ground-Truth Format

```yaml
scenario_id: STR
artifact_id: STR
artifact_type: STR
expected_action: regenerate | preserve | validate_only | human_review
justification: STR
annotator_id: STR
confidence: 1-5
adjudicated: bool
final_action: STR  # after adjudication if needed
```

## 8. Publication

Ground-truth annotations included in the replication package. Annotator identities may be anonymized. Adjudication records included.
