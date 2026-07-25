from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from benchmark.core.exceptions import ModelBackendError
from benchmark.core.models import LLMResponse, TokenUsage

if TYPE_CHECKING:
    import torch

logger = logging.getLogger(__name__)

_KAGGLE_MODEL_BASE = "/kaggle/input"
_LOCAL_MODEL_FORBIDDEN = True

_MINIMUM_COMPUTE_CAPABILITY = (7, 0)


def _gpu_info() -> dict[str, object]:
    """Collect safe GPU diagnostics without logging secrets or prompts."""
    try:
        import torch
    except ImportError:
        return {"available": False}

    if not torch.cuda.is_available():
        return {"available": False}

    info: dict[str, object] = {
        "available": True,
        "gpu_name": torch.cuda.get_device_name(0),
    }
    try:
        info["cuda_version"] = torch.version.cuda
    except Exception:
        info["cuda_version"] = "unknown"
    try:
        info["pytorch_version"] = torch.__version__
    except Exception:
        info["pytorch_version"] = "unknown"
    try:
        capability = torch.cuda.get_device_capability(0)
        info["compute_capability"] = f"{capability[0]}.{capability[1]}"
        info["compute_capability_tuple"] = capability
    except Exception:
        info["compute_capability"] = "unknown"
        info["compute_capability_tuple"] = (0, 0)

    return info


def _check_gpu_compatibility() -> None:
    """Preflight check: fail if the PyTorch CUDA build cannot execute on the selected GPU.

    The Kaggle environment emitted:
      'Tesla P100 compute capability sm_60 is not supported by the installed
       PyTorch build, which supports sm_70 and newer.'

    This is a blocking error — generation would silently produce garbage or crash.
    """
    import torch

    if not torch.cuda.is_available():
        return

    capability = torch.cuda.get_device_capability(0)
    if capability < _MINIMUM_COMPUTE_CAPABILITY:
        gpu_name = torch.cuda.get_device_name(0)
        raise ModelBackendError(
            f"GPU compute capability {capability[0]}.{capability[1]} on {gpu_name} "
            f"is below the minimum {_MINIMUM_COMPUTE_CAPABILITY[0]}.{_MINIMUM_COMPUTE_CAPABILITY[1]} "
            f"required by the installed PyTorch build. "
            f"PyTorch CUDA version: {torch.version.cuda}. "
            f"Select a Kaggle accelerator with sm_70+ (e.g. T4, V100, A100) "
            f"or use a PyTorch build that supports sm_60."
        )


@dataclass(frozen=True)
class GpuPreflightResult:
    """Result of a GPU compatibility preflight check.

    The caller must use this to decide whether to proceed with LLM-backed
    strategy execution.  A failed preflight must NOT create a scientific
    RunRecord — it is an engineering-gate result.
    """
    compatible: bool
    hardware_identity: str
    software_identity: str
    gpu_name: str = ""
    compute_capability: str = ""
    cuda_version: str = ""
    pytorch_version: str = ""
    rejection_reason: str = ""


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
        logger.info("MODEL_INITIALIZATION_STARTED model=%s", model_name)

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        logger.info("GENERATION_STARTED max_tokens=%d temperature=%s", max_tokens, temperature)
        try:
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

            logger.info(
                "GENERATION_SUCCEEDED prompt_tokens=%d completion_tokens=%d total_tokens=%d",
                prompt_tokens, completion_tokens, prompt_tokens + completion_tokens,
            )
            return LLMResponse(
                text=output_text,
                token_usage=TokenUsage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens,
                ),
                finish_reason="stop",
            )
        except ModelBackendError:
            raise
        except Exception as exc:
            gpu = _gpu_info()
            logger.error(
                "GENERATION_FAILED exception=%s gpu=%s",
                type(exc).__name__, gpu.get("gpu_name", "unknown"),
            )
            raise ModelBackendError(
                f"Qwen generation failed: {type(exc).__name__}: {exc}"
            ) from exc

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
        from transformers import AutoModelForCausalLM, AutoTokenizer

        model_path = self._resolve_model_path()
        logger.info("Loading model from %s", model_path)

        _check_gpu_compatibility()

        resolved_dtype = self._resolve_dtype()
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

        gpu_info = _gpu_info()
        gpu_name = gpu_info.get("gpu_name", "cpu") if gpu_info.get("available") else "cpu"
        logger.info(
            "MODEL_INITIALIZATION_SUCCEEDED model=%s device=%s gpu=%s dtype=%s",
            self._model_name, device, gpu_name, resolved_dtype,
        )

    def _resolve_dtype(self) -> torch.dtype:
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

    @staticmethod
    def preflight() -> GpuPreflightResult:
        """Check GPU compatibility without loading the model.

        Returns a GpuPreflightResult that the caller uses to decide
        whether to proceed.  This must NOT create a RunRecord — it is
        an engineering-gate check that runs before scientific execution.
        """
        from benchmark.checkpoint.persistence import (
            detect_hardware_identity,
            detect_software_environment_identity,
        )

        hw = detect_hardware_identity()
        sw = detect_software_environment_identity()

        try:
            import torch
        except ImportError:
            return GpuPreflightResult(
                compatible=False,
                hardware_identity=hw,
                software_identity=sw,
                rejection_reason="PyTorch is not installed",
            )

        if not torch.cuda.is_available():
            return GpuPreflightResult(
                compatible=False,
                hardware_identity=hw,
                software_identity=sw,
                gpu_name="cpu",
                rejection_reason="CUDA GPU required for the configured Qwen backend.",
            )

        gpu_name = torch.cuda.get_device_name(0)
        capability = torch.cuda.get_device_capability(0)
        cap_str = f"{capability[0]}.{capability[1]}"
        cuda_ver = str(getattr(torch.version, "cuda", "unknown"))
        torch_ver = torch.__version__

        compatible = capability >= _MINIMUM_COMPUTE_CAPABILITY
        rejection = "" if compatible else (
            f"GPU compute capability {cap_str} on {gpu_name} "
            f"is below minimum {_MINIMUM_COMPUTE_CAPABILITY[0]}.{_MINIMUM_COMPUTE_CAPABILITY[1]} "
            f"required by installed PyTorch build (torch={torch_ver}, cuda={cuda_ver}). "
            "An LLM-dependent Run must not proceed on this hardware."
        )

        return GpuPreflightResult(
            compatible=compatible,
            hardware_identity=hw,
            software_identity=sw,
            gpu_name=gpu_name,
            compute_capability=cap_str,
            cuda_version=cuda_ver,
            pytorch_version=torch_ver,
            rejection_reason=rejection,
        )
