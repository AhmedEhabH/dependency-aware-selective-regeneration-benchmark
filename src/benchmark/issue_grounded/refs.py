"""Issue-grounded intent headroom - reference parsing + resolution (T3).

Deterministic reference resolution for DEVELOPMENT tasks:

1. parse `#NNNN`-style references (3-6 digit) from a commit message;
2. resolve each referenced object in the SAME repository (issue vs PR);
3. distinguish ISSUE from PULL REQUEST (REST `pull_request` key);
4. for direct issues keep the issue as the intent candidate;
5. for PRs, PR text is NEVER intent; a linked closing issue is derived from
   (a) GraphQL `closingIssuesReferences`, and if empty, (b) `#NNNN`
   references in the PR title/body that resolve to ISSUE objects in the same
   repo. This is dataset-construction linkage only.

Provenance categories (mutually exclusive, per task):
- DIRECT_ISSUE      : a referenced object is directly an issue.
- PR_ONE_LINKED     : referenced objects are PRs; total linked issues == 1.
- PR_MULTI_LINKED   : referenced objects are PRs; total linked issues > 1.
- PR_NO_LINKED      : referenced objects are PRs; no linked issue resolved.
- UNRESOLVED        : no ref parsed OR every ref failed to resolve.

ZERO expensive/irreversible behavior. Pure + deterministic given the cache.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from benchmark.issue_grounded.github import GitHubClient, _closing_issues_for

REF_RE = re.compile(r"#(\d{3,6})\b")
OWNER_BY_REPO = {"djangocms": "django-cms", "saleor": "saleor"}
REPO_BY_NAME = {"djangocms": "django-cms", "saleor": "saleor"}

PROV_DIRECT = "DIRECT_ISSUE"
PROV_PR_ONE = "PR_ONE_LINKED"
PROV_PR_MULTI = "PR_MULTI_LINKED"
PROV_PR_NONE = "PR_NO_LINKED"
PROV_UNRESOLVED = "UNRESOLVED"
PROV_EMPTY = "NO_REFERENCE"


@dataclass(frozen=True)
class ResolvedRef:
    number: int
    kind: str  # "issue" | "pr"
    title: str
    body: str
    created_at: str
    updated_at: str
    html_url: str
    repository: str
    owner: str
    repo_name: str


@dataclass(frozen=True)
class TaskResolution:
    case_id: str
    repository: str
    ref_numbers: tuple[int, ...]
    provenance: str
    direct_issues: tuple[ResolvedRef, ...]
    linked_issues: tuple[ResolvedRef, ...]
    pr_without_linked: tuple[ResolvedRef, ...]
    unresolved: tuple[int, ...]
    raw_refs: tuple[dict[str, Any], ...]  # storage for corpus freeze

    @property
    def all_issue_candidates(self) -> tuple[ResolvedRef, ...]:
        """Direct issues + linked issues, deduped by (repo, number)."""
        seen: set[tuple[str, str, int]] = set()
        out: list[ResolvedRef] = []
        for r in (*self.direct_issues, *self.linked_issues):
            key = (r.repository, r.repo_name, r.number)
            if key in seen:
                continue
            seen.add(key)
            out.append(r)
        return tuple(sorted(out, key=lambda r: (r.repository, r.number)))


def parse_refs(commit_message: str) -> tuple[int, ...]:
    """All distinct #NNNN numbers in the commit message, ascending order."""
    return tuple(sorted({int(n) for n in REF_RE.findall(commit_message or "")}))


def _to_resolved(raw: dict[str, Any], owner: str, repo_name: str, repository: str) -> ResolvedRef:
    return ResolvedRef(
        number=int(raw.get("number", 0)),
        kind="pr" if raw.get("pull_request") else "issue",
        title=str(raw.get("title") or ""),
        body=str(raw.get("body") or ""),
        created_at=str(raw.get("created_at") or ""),
        updated_at=str(raw.get("updated_at") or ""),
        html_url=str(raw.get("html_url") or ""),
        repository=repository,
        owner=owner,
        repo_name=repo_name,
    )


def _resolve_ref(client: GitHubClient, repository: str, number: int) -> dict[str, Any] | None:
    owner = OWNER_BY_REPO[repository]
    repo_name = REPO_BY_NAME[repository]
    return client.issue_or_pr(owner, repo_name, number)


def _linked_from_pr(client: GitHubClient, pr_raw: dict[str, Any],
                    repository: str) -> list[ResolvedRef]:
    """Linked closing issues for a PR (dataset-construction linkage only).

    1. GraphQL closingIssuesReferences; 2. if empty, `#NNNN` references in the
    PR title/body that resolve to ISSUE objects in the same repository.
    Deterministic; PR text never becomes intent.
    """
    owner = OWNER_BY_REPO[repository]
    repo_name = REPO_BY_NAME[repository]
    pr_number = int(pr_raw.get("number", 0))
    out: list[ResolvedRef] = []

    gql = _closing_issues_for(client, owner, repo_name, pr_number)
    for node in gql:
        if not node or not node.get("number"):
            continue
        out.append(
            ResolvedRef(
                number=int(node["number"]),
                kind="issue",
                title=str(node.get("title") or ""),
                body=str(node.get("body") or ""),
                created_at=str(node.get("createdAt") or ""),
                updated_at=str(node.get("updatedAt") or ""),
                html_url=f"https://github.com/{owner}/{repo_name}/issues/{node['number']}",
                repository=repository,
                owner=owner,
                repo_name=repo_name,
            )
        )

    if out:
        return out

    # Fallback: PR title/body #NNNN references that resolve to ISSUE objects.
    text = f"{pr_raw.get('title') or ''}\n{pr_raw.get('body') or ''}"
    for number in parse_refs(text):
        obj = client.issue_or_pr(owner, repo_name, number)
        if not obj or obj.get("pull_request") is not None:
            continue  # is a PR or not found - not a direct linked issue
        out.append(_to_resolved(obj, owner, repo_name, repository))

    # Dedupe + sort ascending by number.
    seen: set[int] = set()
    uniq: list[ResolvedRef] = []
    for r in sorted(out, key=lambda r: r.number):
        if r.number in seen:
            continue
        seen.add(r.number)
        uniq.append(r)
    return uniq


def resolve_task(
    client: GitHubClient, case_id: str, repository: str, intent_text: str
) -> TaskResolution:
    """Resolve a single task's commit-message references deterministically."""
    numbers = parse_refs(intent_text)
    if not numbers:
        return TaskResolution(
            case_id=case_id, repository=repository, ref_numbers=(),
            provenance=PROV_EMPTY, direct_issues=(), linked_issues=(),
            pr_without_linked=(), unresolved=(), raw_refs=[],
        )

    refs_raw: list[dict[str, Any]] = []
    direct: list[ResolvedRef] = []
    linked: list[ResolvedRef] = []
    pr_no_link: list[ResolvedRef] = []
    unresolved: list[int] = []
    pr_refs: list[dict[str, Any]] = []

    for n in numbers:
        raw = _resolve_ref(client, repository, n)
        if raw is None:
            unresolved.append(n)
            continue
        item = {"number": n, "kind": "pr" if raw.get("pull_request") else "issue",
                "repository": repository,
                "title": raw.get("title"), "body": raw.get("body"),
                "created_at": raw.get("created_at"), "updated_at": raw.get("updated_at"),
                "html_url": raw.get("html_url")}
        refs_raw.append(item)
        if raw.get("pull_request"):
            pr_refs.append(raw)
            pr_linked = _linked_from_pr(client, raw, repository)
            if pr_linked:
                linked.extend(pr_linked)
            else:
                pr_no_link.append(_to_resolved(raw, OWNER_BY_REPO[repository],
                                               REPO_BY_NAME[repository], repository))
        else:
            direct.append(_to_resolved(raw, OWNER_BY_REPO[repository],
                                       REPO_BY_NAME[repository], repository))

    n_linked = len({r.number for r in linked})
    if direct:
        prov = PROV_DIRECT
    elif linked and n_linked == 1:
        prov = PROV_PR_ONE
    elif linked and n_linked > 1:
        prov = PROV_PR_MULTI
    elif pr_no_link and not unresolved:
        prov = PROV_PR_NONE
    elif unresolved and not direct and not linked and not pr_no_link:
        prov = PROV_UNRESOLVED
    elif unresolved:
        # mix of unresolved refs and PRs without linked issues: classify by
        # the strongest signal available.
        prov = PROV_PR_NONE if pr_no_link else PROV_UNRESOLVED
    else:
        prov = PROV_UNRESOLVED

    return TaskResolution(
        case_id=case_id, repository=repository, ref_numbers=numbers,
        provenance=prov, direct_issues=tuple(direct), linked_issues=tuple(linked),
        pr_without_linked=tuple(pr_no_link), unresolved=tuple(unresolved),
        raw_refs=refs_raw,
    )


def save_resolutions(path: Path, resolutions: list[TaskResolution]) -> None:
    payload = [
        {
            "case_id": r.case_id,
            "repository": r.repository,
            "ref_numbers": list(r.ref_numbers),
            "provenance": r.provenance,
            "direct_issues": [_ref_json(x) for x in r.direct_issues],
            "linked_issues": [_ref_json(x) for x in r.linked_issues],
            "pr_without_linked": [_ref_json(x) for x in r.pr_without_linked],
            "unresolved": list(r.unresolved),
        }
        for r in resolutions
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=1), encoding="utf-8")


def _ref_json(r: ResolvedRef) -> dict[str, Any]:
    return {
        "number": r.number, "kind": r.kind, "title": r.title, "body": r.body,
        "created_at": r.created_at, "updated_at": r.updated_at, "html_url": r.html_url,
        "repository": r.repository, "owner": r.owner, "repo_name": r.repo_name,
    }
