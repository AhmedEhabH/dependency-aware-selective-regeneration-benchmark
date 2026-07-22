from __future__ import annotations

import logging
from pathlib import Path

from benchmark.core.exceptions import ModelBackendError
from benchmark.core.models import LLMResponse, TokenUsage

logger = logging.getLogger(__name__)

_KAGGLE_MODEL_BASE = "/kaggle/input"
_LOCAL_MODEL_FORBIDDEN = True


class KaggleQwenBackend:
    def __init__(
        self,
        model_name: str = "qwen2.5-coder",
        model_path: str | None = None,
        device: str | None = None,
        dtype: str | None = None,
    ) -> None:
        self._model_name = model_name
        self._model_path = model_path
        self._device = device
        self._dtype = dtype
        self._model = None
        self._tokenizer = None
        self._loaded = False

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        self._ensure_loaded()
        assert self._model is not None
        assert self._tokenizer is not None

        import torch

        inputs = self._tokenizer(prompt, return_tensors="pt")
        input_ids = inputs["input_ids"].to(self._model.device)
        attention_mask = inputs.get("attention_mask")
        if attention_mask is not None:
            attention_mask = attention_mask.to(self._model.device)

        prompt_tokens = input_ids.shape[1]

        gen_kwargs: dict[str, object] = {
            "input_ids": input_ids,
            "max_new_tokens": max_tokens,
            "do_sample": temperature > 0.0,
        }
        if attention_mask is not None:
            gen_kwargs["attention_mask"] = attention_mask
        if temperature > 0.0:
            gen_kwargs["temperature"] = temperature
            gen_kwargs["top_p"] = 0.95

        with torch.no_grad():
            output_ids = self._model.generate(**gen_kwargs)

        generated_ids = output_ids[0, prompt_tokens:]
        output_text = self._tokenizer.decode(generated_ids, skip_special_tokens=True)
        completion_tokens = generated_ids.shape[0]

        return LLMResponse(
            text=output_text,
            token_usage=TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
            finish_reason="stop",
        )

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._lazy_import()
        self._load_model()

    def _lazy_import(self) -> None:
        try:
            import torch  # noqa: F401
            import transformers  # noqa: F401
        except ImportError as exc:
            raise ModelBackendError(
                "KaggleQwenBackend requires torch and transformers. "
                "These are Kaggle-only dependencies and must not be installed locally."
            ) from exc

    def _resolve_model_path(self) -> Path:
        if self._model_path:
            p = Path(self._model_path)
            if p.is_dir():
                return p
            raise ModelBackendError(f"Model path does not exist: {p}")

        kaggle_input = Path(_KAGGLE_MODEL_BASE)
        if kaggle_input.is_dir():
            candidates = sorted(kaggle_input.iterdir())
            for candidate in candidates:
                if candidate.is_dir() and self._model_name.lower() in candidate.name.lower():
                    logger.info("Discovered Kaggle model at %s", candidate)
                    return candidate
            for candidate in candidates:
                if candidate.is_dir():
                    logger.info("Using Kaggle model at %s", candidate)
                    return candidate

        raise ModelBackendError(
            f"Cannot locate model '{self._model_name}' in {_KAGGLE_MODEL_BASE}. "
            "Ensure the Qwen model dataset is added to this Kaggle notebook."
        )

    def _load_model(self) -> None:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        model_path = self._resolve_model_path()
        logger.info("Loading model from %s", model_path)

        resolved_dtype = self._resolve_dtype()  # type: ignore[no-untyped-call]
        device = self._resolve_device()

        self._tokenizer = AutoTokenizer.from_pretrained(
            str(model_path),
            trust_remote_code=True,
            local_files_only=True,
        )
        self._model = AutoModelForCausalLM.from_pretrained(
            str(model_path),
            torch_dtype=resolved_dtype,
            device_map=device,
            trust_remote_code=True,
            local_files_only=True,
        )
        assert self._model is not None
        self._model.eval()
        self._loaded = True

        gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu"
        logger.info(
            "Model loaded: %s on %s (dtype=%s)",
            self._model_name,
            gpu_name,
            resolved_dtype,
        )

    def _resolve_dtype(self):  # type: ignore[no-untyped-def]  # type: ignore[no-untyped-def]
        import torch

        if self._dtype:
            return getattr(torch, self._dtype)
        if torch.cuda.is_available():
            capability = torch.cuda.get_device_capability(0)
            if capability[0] >= 8:
                return torch.bfloat16
            return torch.float16
        return torch.float32

    def _resolve_device(self) -> str:
        if self._device:
            return self._device
        import torch

        if torch.cuda.is_available():
            return "cuda"
        return "cpu"
