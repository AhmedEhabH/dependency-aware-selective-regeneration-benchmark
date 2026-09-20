"""Issue-grounded intent headroom - deterministic GitHub retrieval client (T3).

Retrieves GitHub issue / PR metadata with:
  - bearer-token auth (from env GH_TOKEN / GITHUB_TOKEN, or `gh auth token`);
  - exponential backoff retries for transient network failures (the live
    api.github.com path is intermittently flaky on this workstation);
  - an on-disk JSON cache keyed by endpoint so a run never re-fetches the
    same object (deterministic, budgeting-friendly);

ZERO expensive/irreversible behavior. Only GET-style reads through the public
REST + GraphQL API. No writes to GitHub. No comments / diffs / PR texts are
downloaded.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

REST_BASE = "https://api.github.com"
GRAPHQL = "https://api.github.com/graphql"
GITHUB_ACCEPT = "application/vnd.github+json"
API_VERSION = "2022-11-28"

MAX_ATTEMPTS = 14
BACKOFF_BASE_S = 2.0


def _bearer_token() -> str:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
    if token:
        return token
    proc = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True)
    if proc.returncode == 0 and proc.stdout.strip():
        return proc.stdout.strip()
    raise RuntimeError("no GitHub token available (GH_TOKEN / GITHUB_TOKEN / gh auth)")


def _request_json(url: str, *, token: str, payload: dict[str, Any] | None = None) -> dict[str, Any] | None:
    data = None
    headers: dict[str, str] = {
        "Authorization": f"Bearer {token}",
        "Accept": GITHUB_ACCEPT,
        "X-GitHub-Api-Version": API_VERSION,
        "User-Agent": "selective-regen-benchmark-research",
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    last_err: Exception | None = None
    for attempt in range(MAX_ATTEMPTS):
        req = urllib.request.Request(url, data=data, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                return body
        except urllib.error.HTTPError as exc:
            # 404 = the referenced object does not exist (unresolved reference).
            if exc.code == 404:
                return None
            # Other 4xx are permanent; do not retry forever.
            if exc.code not in (403, 429):
                raise
            last_err = exc
        except Exception as exc:
            last_err = exc
        time.sleep(BACKOFF_BASE_S ** attempt)
    raise RuntimeError(f"GitHub fetch failed after {MAX_ATTEMPTS} attempts: {url} ({last_err})")


class GitHubClient:
    """Retrying REST + GraphQL GitHub client with an on-disk cache."""

    def __init__(self, cache_dir: Path, token: str | None = None) -> None:
        self.token = token or _bearer_token()
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, Any] = {}
        self._cache_path = self.cache_dir / "github_cache.json"
        if self._cache_path.exists():
            self._cache = json.loads(self._cache_path.read_text(encoding="utf-8"))

    def _persist(self) -> None:
        self._cache_path.write_text(json.dumps(self._cache), encoding="utf-8")

    def rest(self, path: str) -> dict[str, Any] | None:
        key = f"rest::{path}"
        if key in self._cache:
            return self._cache[key]
        result = _request_json(f"{REST_BASE}{path}", token=self.token)
        self._cache[key] = result
        self._persist()
        return result

    def graphql(self, query: str, variables: dict[str, Any]) -> dict[str, Any] | None:
        key = f"gql::{query}::{json.dumps(variables, sort_keys=True)}"
        if key in self._cache:
            return self._cache[key]
        result = _request_json(GRAPHQL, token=self.token, payload={"query": query, "variables": variables})
        self._cache[key] = result
        self._persist()
        return result

    def issue_or_pr(self, owner: str, repo: str, number: int) -> dict[str, Any] | None:
        """GET /repos/{o}/{r}/issues/{n} - returns both issues and PRs (PRs
        carry a `pull_request` key)."""
        return self.rest(f"/repos/{owner}/{repo}/issues/{number}")


def _closing_issues_for(client: GitHubClient, owner: str, repo: str, pr_number: int) -> list[dict[str, Any]]:
    query = (
        f'query {{ repository(owner: "{owner}", name: "{repo}") {{'
        + f"pullRequest(number: {pr_number}) {{"
        + "closingIssuesReferences(first: 20) { nodes { number title body createdAt updatedAt } }"
        + "} } }"
    )
    data = client.graphql(query, {})
    if not data or "data" not in data or data["data"] is None:
        return []
    repo_node = data["data"].get("repository") or {}
    pr_node = repo_node.get("pullRequest") or {}
    nodes = (pr_node.get("closingIssuesReferences") or {}).get("nodes") or []
    return [dict(n or {}) for n in nodes]
