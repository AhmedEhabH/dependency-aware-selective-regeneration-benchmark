from __future__ import annotations

from benchmark.core.exceptions import ModelBackendError
from benchmark.core.models import LLMResponse


class KaggleQwenBackend:
    def __init__(self, model_name: str = "Qwen/Qwen2.5-72B-Instruct") -> None:
        self._model_name = model_name
        self._model = None
        self._tokenizer = None

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        self._lazy_import()
        if self._model is None or self._tokenizer is None:
            raise ModelBackendError("Kaggle Qwen model not initialized")
        raise ModelBackendError(
            "KaggleQwenBackend.generate() is a skeleton for Kaggle execution only. "
            "Real inference requires torch, transformers, and GPU (Kaggle environment). "
            "Do not call this method in local engineering validation."
        )

    def _lazy_import(self) -> None:
        if self._model is not None:
            return
        try:
            import torch  # noqa: F401
            import transformers  # noqa: F401
        except ImportError as exc:
            raise ModelBackendError(
                "KaggleQwenBackend requires torch and transformers. "
                "These are Kaggle-only dependencies and must not be installed locally."
            ) from exc
