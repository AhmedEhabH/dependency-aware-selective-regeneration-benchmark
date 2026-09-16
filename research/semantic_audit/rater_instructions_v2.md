# Semantic-Proxy Human Audit — Rater Instructions (two-rater)

For EACH file in the packet, assign ONE category:
- 1_required: semantically required for the stated change
- 2_related_optional: semantically related/optional for the stated change
- 3_incidental_tangled: incidental / tangled co-change (refactor, cleanup, unrelated)
- 4_not_determinable: not determinable from the provided evidence

Base the judgment on the public intent, the parent source context,
the P->T diff, and the observed changed files. The changed-file set
need not be minimal. Flag ambiguity rather than guessing.
AI/machine notes in the packets are preliminary only and are NOT
authoritative for your judgment.

Use the blank Rater form (A or B). Do NOT open INTERNAL_TEST or RESERVE.