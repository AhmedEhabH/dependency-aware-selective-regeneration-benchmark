"""Pinned SweRankEmbed-Small loader + deterministic embedding cache (T3, ZERO API).

The model revision is PINNED (never `main`):

  model_id     = "Salesforce/SweRankEmbed-Small"
  revision     = "745d2a06103a66d3cfa600aa52fc0d3523010daa"   (2025-06-24)
  license      = CC-BY-NC-4.0
  params       = 137M (0.1B); architecture NomicBertModel (12L/768H/12heads,
                 8192 context); embedding dim 768; CLS pooling;
                 query prompt "Represent this query for searching relevant code: "
  artifact     = model.safetensors 273,474,944 bytes (SHA-256 recorded by the run)
  interface    = SentenceTransformer(trust_remote_code=True),
                 max_seq_length = 1024 (official SweRank eval default)

Embeddings are L2-normalized so the frozen adapter's score = cosine.

A deterministic disk cache maps unit_sha256 -> embedding row (float32 npy +
JSON index). Re-running with the same pinned model + same input blobs is
byte-deterministic. NO network call happens at inference time (model is loaded
from the local HF cache).
"""
from __future__ import annotations

import json
import os
from collections.abc import Sequence
from pathlib import Path

import numpy as np

MODEL_ID = "Salesforce/SweRankEmbed-Small"
MODEL_REVISION = "745d2a06103a66d3cfa600aa52fc0d3523010daa"
QUERY_PROMPT_NAME = "query"
MAX_SEQ_LENGTH = 1024
EMBED_DIM = 768


class SweRankEmbed:
    """Thin wrapper: load pinned model once, encode queries/units, cache on disk."""

    def __init__(self, cache_dir: Path, hf_home: Path | None = None) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self.cache_dir / "embed_index.json"
        self._data_path = self.cache_dir / "embeddings.npy"
        self._index: dict[str, int] = {}
        self._matrix: np.ndarray | None = None
        if self._index_path.exists() and self._data_path.exists():
            self._index = json.loads(self._index_path.read_text(encoding="utf-8"))
            self._matrix = np.load(self._data_path)
        if hf_home is not None:
            os.environ.setdefault("HF_HOME", str(hf_home))
            os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(
            MODEL_ID, trust_remote_code=True, revision=MODEL_REVISION
        )
        self._model.max_seq_length = MAX_SEQ_LENGTH

    # -- persistence -------------------------------------------------------
    def _flush(self) -> None:
        if self._matrix is None:
            return
        self._data_path.parent.mkdir(parents=True, exist_ok=True)
        np.save(self._data_path, self._matrix)
        self._index_path.write_text(
            json.dumps(self._index, sort_keys=True), encoding="utf-8"
        )

    # -- encoding ----------------------------------------------------------
    def encode_query(self, text: str) -> np.ndarray:
        v = self._model.encode([text], prompt_name=QUERY_PROMPT_NAME)
        return _l2(v[0])

    def encode_units(self, units: Sequence[str]) -> dict[str, np.ndarray]:
        """Encode units, serving from the disk cache. Returns key -> vector."""
        missing = [u for u in units if _sha(u) not in self._index]
        if missing:
            vecs = self._model.encode(list(missing), batch_size=64, show_progress_bar=False)
            base = int(self._matrix.shape[0]) if self._matrix is not None else 0
            new_mat = np.zeros((base + len(missing), EMBED_DIM), dtype=np.float32)
            if self._matrix is not None:
                new_mat[:base] = self._matrix
            for j, (u, v) in enumerate(zip(missing, vecs, strict=True)):
                key = _sha(u)
                self._index[key] = base + j
                new_mat[base + j] = _l2(v)
            self._matrix = new_mat
            self._flush()
        return {_sha(u): self._matrix[self._index[_sha(u)]] for u in units}

    @property
    def n_cached(self) -> int:
        return len(self._index)

    @property
    def cache_bytes(self) -> int:
        return self._data_path.stat().st_size if self._data_path.exists() else 0


def _sha(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def _l2(v: np.ndarray) -> np.ndarray:
    arr = np.asarray(v, dtype=np.float32)
    n = float(np.linalg.norm(arr))
    return arr / n if n > 0 else arr
