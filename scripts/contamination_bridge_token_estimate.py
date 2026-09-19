"""Informational DEVELOPMENT token estimate for the contamination-bridge budget annex.

Regenerates the frozen code-unit texts (49,705) from the cached parent-revision
blob texts using the frozen extraction rule, counts Qwen-family tokens for the
unit corpus and the 323 DEVELOPMENT queries, and records the numbers to
research/contamination-bridge/token_estimate.json.

ZERO API calls. The bridge is STOPPED before call 1 (model unavailable), so
this is planning information only.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from benchmark.recall.data import load_dev_tasks  # noqa: E402
from benchmark.signal.code_units import extract_code_units, sha256_text  # noqa: E402

BLOB_CACHE = Path(r"C:\Users\Ahmed\AppData\Local\Temp\opencode\swerank-cache\blob_text.json")
OUT = _PROJECT_DIR / "research" / "contamination-bridge" / "token_estimate.json"


def main() -> int:
    blob_texts = json.loads(BLOB_CACHE.read_text(encoding="utf-8"))
    units: dict[str, str] = {}
    for _sha, text in blob_texts.items():
        if text is None:
            continue
        for u in extract_code_units(text):
            units.setdefault(sha256_text(u), u)
    unit_texts = list(units.values())
    print("distinct units:", len(unit_texts))

    # Load a Qwen tokenizer for counting (free; no inference).
    tokenizer = None
    tokenizer_id = None
    try:
        from transformers import AutoTokenizer
        for mid in ("Qwen/Qwen3-Embedding-8B", "Qwen/Qwen2.5-7B-Instruct"):
            try:
                tokenizer = AutoTokenizer.from_pretrained(mid, trust_remote_code=True)
                tokenizer_id = mid
                break
            except Exception:
                continue
    except Exception:
        tokenizer = None
    print("tokenizer:", tokenizer_id)

    def count(text: str) -> int:
        if tokenizer is not None:
            return len(tokenizer(text, add_special_tokens=True)["input_ids"])
        return max(1, len(text) // 4)  # conservative fallback

    unit_token_counts = [count(u) for u in unit_texts]
    unit_tokens = sum(unit_token_counts)

    tasks = load_dev_tasks()
    queries = [t.intent_text for t in tasks]
    query_token_counts = [count(q) for q in queries]
    query_tokens = sum(query_token_counts)

    def pct(xs, p):
        xs = sorted(xs)
        i = min(len(xs) - 1, int(p / 100 * len(xs)))
        return xs[i]

    out = {
        "label": "INFORMATIONAL ANNEX — bridge STOPPED before call 1 (model unavailable)",
        "tokenizer": tokenizer_id or "fallback len//4",
        "n_units": len(unit_texts),
        "n_queries": len(queries),
        "unit_tokens_total": unit_tokens,
        "unit_tokens_p50": pct(unit_token_counts, 50),
        "unit_tokens_p90": pct(unit_token_counts, 90),
        "unit_tokens_p99": pct(unit_token_counts, 99),
        "unit_tokens_max": max(unit_token_counts),
        "query_tokens_total": query_tokens,
        "query_tokens_mean": round(query_tokens / len(queries), 1),
        "combined_tokens_total": unit_tokens + query_tokens,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
