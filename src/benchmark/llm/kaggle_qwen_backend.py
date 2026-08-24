from __future__ import annotations

import gc
import hashlib
import json
import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from benchmark.core.exceptions import ModelBackendError
from benchmark.core.models import LLMResponse, TokenUsage

logger = logging.getLogger(__name__)

_KAGGLE_MODEL_BASE = "/kaggle/input"
_LOCAL_MODEL_FORBIDDEN = True

_MINIMUM_COMPUTE_CAPABILITY = (7, 0)

CANONICAL_ALLOC_CONF = "expandable_segments:True"

CANONICAL_QUANTIZATION_MODES = ("bnb-int8", "bnb-nf4", "fp16")

KAGGLE_CACHE_IMPLEMENTATION = "offloaded"

# V0.9.22 long-context attention memory closure: the effective runtime
# attention path must be SDPA with a fail-closed fused-kernel policy on CUDA.
# Target evidence: the v0.9.21 real 12,044-token probe attempted a
# 21.62 GiB allocation == the full float32 40-head 12044x12044 attention
# score matrix, i.e. the quadratic math/eager fallback had materialized.
KAGGLE_ATTENTION_IMPLEMENTATION = "sdpa"

KAGGLE_SDPA_KERNEL_POLICY = "flash_or_efficient_no_math"

# Prompts at or above this token count classify a generation OOM as a
# prompt-prefill attention failure rather than a completion-budget failure.
LONG_PROMPT_PREFILL_OOM_TOKEN_THRESHOLD = 2048

_QUANTIZATION_METHOD_SAFE = frozenset({"bitsandbytes", "bnb"})

NF4_LOAD_CONFIG = {
    "load_in_4bit": True,
    "bnb_4bit_quant_type": "nf4",
    "bnb_4bit_compute_dtype": "float16",
    "bnb_4bit_use_double_quant": True,
}

SYSTEM_TRANSFORMATION_MESSAGE = (
    "You are a precise source-code transformation engine. Follow every scope, "
    "architecture, and output constraint literally. Make minimal edits, preserve "
    "unrelated behavior, never invent undeclared dependencies, and return only the "
    "requested complete artifact content."
)


def _set_canonical_alloc_conf() -> None:
    """Set the canonical PyTorch memory allocation environment variable.

    ``PYTORCH_ALLOC_CONF=expandable_segments:True`` must be set before torch is
    imported. The older ``PYTORCH_CUDA_ALLOC_CONF`` alias is left untouched.
    """
    os.environ.setdefault("PYTORCH_ALLOC_CONF", CANONICAL_ALLOC_CONF)


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


def _empty_cuda_cache() -> None:
    """Best-effort CUDA cache flush; never raises and works without torch."""
    import contextlib

    try:
        import torch
    except Exception:
        return
    with contextlib.suppress(Exception):
        torch.cuda.empty_cache()


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


def _read_checkpoint_config(model_path: Path) -> dict[str, Any]:
    """Read and validate ``config.json`` from a checkpoint directory."""
    if not model_path.is_dir():
        raise ModelBackendError(f"Model path does not exist: {model_path}")
    config_file = model_path / "config.json"
    if not config_file.is_file():
        raise ModelBackendError(f"Model path missing config.json: {model_path}")
    try:
        data = json.loads(config_file.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ModelBackendError(f"Failed to read model config.json: {exc}") from exc
    if not isinstance(data, dict):
        raise ModelBackendError(f"Model config.json is not a JSON object: {model_path}")
    return data


def _checkpoint_quantization_method(config: dict[str, Any]) -> str:
    """Extract a checkpoint's declared quantization method, lowercased.

    Returns ``""`` for unquantized checkpoints. Sources (in precedence order):
    ``quantization_config.quant_method``, ``quantization_config.quantization_method``,
    ``quantization_config.quant_type``.
    """
    qconf = config.get("quantization_config")
    if not isinstance(qconf, dict):
        return ""
    method = qconf.get("quant_method") or qconf.get("quantization_method") or qconf.get("quant_type") or ""
    if not isinstance(method, str):
        return ""
    return method.strip().lower()


def _checkpoint_identity_slug(model_path: Path) -> str:
    """Deterministic ASCII-safe checkpoint slug used in model identity.

    A numeric final path component is a Kaggle model-version directory; the
    slug then combines the parent model directory name and the version (for
    example ``14b-instruct-v1``). Any other directory keeps its basename. The
    slug is lowercased and sanitized to ``[a-z0-9._-]`` with any other run of
    characters replaced by ``-``.
    """
    name = model_path.name
    if name.isdigit():
        name = f"{model_path.parent.name}-v{name}"
    return re.sub(r"[^a-z0-9._-]+", "-", name.strip().lower())


def compute_model_identity(model_path: str | Path, quantization_mode: str = "bnb-int8") -> str:
    """Compute a checkpoint-and-quantization-aware Qwen model identity.

    The identity encodes the checkpoint basename, stable config dimensions, the
    requested quantization mode, and a config digest. Two runs must never share
    an identity unless they load the same checkpoint through the same loader —
    this is what blocks auto-resume cross-model contamination.
    """
    if quantization_mode not in CANONICAL_QUANTIZATION_MODES:
        raise ModelBackendError(
            f"Unsupported quantization_mode {quantization_mode!r}; supported modes are "
            f"{', '.join(CANONICAL_QUANTIZATION_MODES)}."
        )
    if not model_path:
        raise ModelBackendError("model_path is required to compute the Kaggle Qwen model identity")
    path = Path(model_path)
    config = _read_checkpoint_config(path)
    slug = _checkpoint_identity_slug(path)
    payload = {
        "checkpoint_basename": slug,
        "model_type": str(config.get("model_type", "")),
        "hidden_size": int(config.get("hidden_size", 0)),
        "num_hidden_layers": int(config.get("num_hidden_layers", 0)),
        "num_attention_heads": int(config.get("num_attention_heads", 0)),
        "requested_quantization_mode": quantization_mode,
        "checkpoint_quantization_method": _checkpoint_quantization_method(config),
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode("utf-8")
    ).hexdigest()[:12]
    return f"qwen:{slug}:{quantization_mode}:cfg-{digest}"


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
    token_accounting_mode: str = "exact_tokenizer"

    def __init__(
        self,
        model_name: str = "qwen2.5-coder",
        model_path: str | None = None,
        device: str | None = None,
        dtype: str | None = None,
        quantization_mode: str = "bnb-int8",
    ) -> None:
        if quantization_mode not in CANONICAL_QUANTIZATION_MODES:
            raise ModelBackendError(
                f"Unsupported quantization_mode {quantization_mode!r}; "
                f"supported modes are {', '.join(CANONICAL_QUANTIZATION_MODES)}. "
                "No fallback is automatic."
            )
        self._model_name = model_name
        self._model_path = model_path
        self._device = device
        self._dtype = dtype
        self._quantization_mode = quantization_mode
        self._model = None
        self._tokenizer = None
        self._loaded = False
        self._model_identity: str | None = None
        if self._model_path:
            self._model_identity = compute_model_identity(self._model_path, quantization_mode)
        logger.info("MODEL_INITIALIZATION_STARTED model=%s quantization=%s", model_name, quantization_mode)

    @property
    def model_identity(self) -> str:
        if self._model_identity is None:
            if not self._model_path:
                raise ModelBackendError(
                    "model_identity is unavailable without a model_path; "
                    "construct KaggleQwenBackend with model_path= pointing at the checkpoint"
                )
            self._model_identity = compute_model_identity(self._model_path, self._quantization_mode)
        return self._model_identity

    @property
    def quantization_mode(self) -> str:
        return self._quantization_mode

    @property
    def requested_attention_implementation(self) -> str:
        """Attention implementation explicitly requested at load time."""
        return KAGGLE_ATTENTION_IMPLEMENTATION

    @property
    def sdpa_kernel_policy(self) -> str:
        """Canonical SDPA kernel policy enforced during CUDA generation."""
        return KAGGLE_SDPA_KERNEL_POLICY

    @property
    def effective_attention_implementation(self) -> str:
        """The model config's effective attention implementation after load."""
        if self._model is None:
            return ""
        config = getattr(self._model, "config", None)
        value = getattr(config, "_attn_implementation", "") or ""
        return str(value)

    @property
    def checkpoint_basename(self) -> str:
        if not self._model_path:
            raise ModelBackendError(
                "checkpoint_basename is unavailable without a model_path"
            )
        return _checkpoint_identity_slug(Path(self._model_path))

    @property
    def checkpoint_quantization_method(self) -> str:
        if not self._model_path:
            raise ModelBackendError(
                "checkpoint_quantization_method is unavailable without a model_path"
            )
        return _checkpoint_quantization_method(_read_checkpoint_config(Path(self._model_path)))

    @property
    def model_memory_footprint_bytes(self) -> int:
        if self._model is None:
            return 0
        return int(self._model.get_memory_footprint())

    @property
    def device_map_summary(self) -> str:
        if self._model is None:
            return ""
        hf_device_map = getattr(self._model, "hf_device_map", None)
        if hf_device_map:
            return str(hf_device_map)
        device = getattr(self._model, "device", None)
        return str(device) if device is not None else ""

    def load(self) -> None:
        """Load the model+tokenizer synchronously (preflight-friendly)."""
        self._ensure_loaded()

    def run_probe(self, max_tokens: int = 64, prompt: str = "def add(a, b):\n    return a + b\n") -> LLMResponse:
        """Deterministic engineering probe generation.

        Engineering evidence only: never counted as scientific model calls or
        tokens. Uses a fixed seed and greedy sampling.

        This runs fully synchronously and MUST never drive its own event loop:
        it is executed inside the already-running ipykernel loop of the pilot
        notebook's model-preflight cell, where ``asyncio.run`` would raise
        ``RuntimeError: asyncio.run() cannot be called from a running event loop``.
        """
        self._ensure_loaded()
        try:
            import torch

            torch.manual_seed(0)
        except Exception:
            pass
        return self._generate_sync(prompt=prompt, temperature=0.0, max_tokens=max_tokens)

    def _tokenize_prompt_for_probe(self, repeated_snippet: str) -> int:
        """Tokenize a probe prompt and return the prompt token count."""
        assert self._tokenizer is not None
        chat_parts_full = [
            {"role": "system", "content": SYSTEM_TRANSFORMATION_MESSAGE},
            {"role": "user", "content": repeated_snippet},
        ]
        formatted = self._tokenizer.apply_chat_template(
            chat_parts_full, tokenize=False, add_generation_prompt=True,
        )
        inputs = self._tokenizer(formatted, return_tensors="pt")
        return int(inputs["input_ids"].shape[1])

    def _compute_probe_repeat_count(
        self,
        target_prompt_tokens: int,
        snippet: str,
    ) -> int:
        """Compute the repetition count that reaches target_prompt_tokens using the ACTUAL tokenizer.

        Uses exponential search then binary search to find the smallest repeat
        count whose tokenized prompt length >= target_prompt_tokens.  Never
        estimates tokens from character length.
        """
        assert self._tokenizer is not None
        chat_parts_base = [
            {"role": "system", "content": SYSTEM_TRANSFORMATION_MESSAGE},
            {"role": "user", "content": snippet},
        ]
        formatted_base = self._tokenizer.apply_chat_template(
            chat_parts_base, tokenize=False, add_generation_prompt=True,
        )
        base_tokens = len(self._tokenizer(formatted_base, return_tensors="pt")["input_ids"][0])

        if base_tokens >= target_prompt_tokens:
            return 1

        lo = 1
        hi = 2
        while self._tokenize_prompt_for_probe(snippet * hi) < target_prompt_tokens:
            lo = hi
            hi *= 2

        while lo < hi:
            mid = (lo + hi) // 2
            if self._tokenize_prompt_for_probe(snippet * mid) >= target_prompt_tokens:
                hi = mid
            else:
                lo = mid + 1
        return lo

    def _gpu_device_count(self) -> int:
        """Return the integer GPU device count, or 0 if CUDA is unavailable."""
        try:
            import torch
            if torch.cuda.is_available():
                return int(torch.cuda.device_count())
        except Exception:
            pass
        return 0

    def run_long_context_probe(
        self,
        target_prompt_tokens: int = 12000,
        max_tokens: int = 64,
    ) -> dict[str, Any]:
        """Long-context engineering stress probe.

        Builds a synthetic deterministic code-like prompt calibrated by the
        ACTUAL tokenizer to reach ``target_prompt_tokens`` prompt tokens, then
        generates ``max_tokens`` output tokens with ``cache_implementation="offloaded"``.

        Engineering evidence only: never creates a scientific RunRecord or
        token accounting entry. Returns a dict with all required evidence
        fields.

        Fails on OOM by raising ``RuntimeError`` so the caller can fail-closed.
        """
        import time

        self._ensure_loaded()
        assert self._tokenizer is not None

        snippet = (
            "def compute_score(items: list[dict], weights: dict[str, float]) -> float:\n"
            "    total = 0.0\n"
            "    for item in items:\n"
            "        key = item.get('category', '')\n"
            "        weight = weights.get(key, 0.0)\n"
            "        total += item.get('value', 0.0) * weight\n"
            "    return total\n\n"
        )

        repeat_count = self._compute_probe_repeat_count(target_prompt_tokens, snippet)
        repeated_snippet = snippet * repeat_count
        prompt_tokens = self._tokenize_prompt_for_probe(repeated_snippet)

        start_time = time.monotonic()
        response = self._generate_sync(
            prompt=repeated_snippet, temperature=0.0, max_tokens=max_tokens,
        )
        elapsed = time.monotonic() - start_time

        gpu_info = _gpu_info()
        peak_allocated: float | None = None
        peak_reserved: float | None = None
        try:
            import torch
            if torch.cuda.is_available():
                peak_allocated = torch.cuda.max_memory_allocated(0) / (1024**3)
                peak_reserved = torch.cuda.max_memory_reserved(0) / (1024**3)
        except Exception:
            pass

        return {
            "passed": response.token_usage.completion_tokens > 0 and prompt_tokens >= target_prompt_tokens,
            "prompt_tokens": prompt_tokens,
            "target_prompt_tokens": target_prompt_tokens,
            "completion_tokens": response.token_usage.completion_tokens,
            "elapsed_seconds": round(elapsed, 3),
            "cache_implementation": KAGGLE_CACHE_IMPLEMENTATION,
            "requested_attn_implementation": self.requested_attention_implementation,
            "effective_attn_implementation": self.effective_attention_implementation,
            "sdpa_kernel_policy": self.sdpa_kernel_policy,
            "gpu_name": gpu_info.get("gpu_name", "unknown"),
            "gpu_count": self._gpu_device_count(),
            "peak_allocated_gib": round(peak_allocated, 3) if peak_allocated is not None else None,
            "peak_reserved_gib": round(peak_reserved, 3) if peak_reserved is not None else None,
            "finish_reason": response.finish_reason,
        }

    def count_prompt_tokens(self, prompt: str) -> int:
        self._ensure_loaded()
        if self._tokenizer is None:
            raise ModelBackendError("KaggleQwenBackend: tokenizer not loaded")
        try:
            chat_prompt = self._format_chat_prompt(prompt)
            return len(self._tokenizer(chat_prompt, return_tensors="pt")["input_ids"][0])
        except Exception as exc:
            raise ModelBackendError(
                f"KaggleQwenBackend: tokenizer counting failed: {exc}"
            ) from exc

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        return self._generate_sync(prompt=prompt, temperature=temperature, max_tokens=max_tokens)

    def _sdpa_kernel_policy_context(self) -> Any:
        """Fail-closed SDPA kernel policy for CUDA generation.

        On CUDA, ``scaled_dot_product_attention`` is restricted to the fused
        FLASH_ATTENTION / EFFICIENT_ATTENTION backends so a long-prompt
        prefill can never silently materialize the quadratic math-fallback
        score matrix (the v0.9.21 target OOM root cause). If the installed
        PyTorch cannot provide the policy API, this raises instead of falling
        back. Non-CUDA execution preserves historical behavior.
        """
        import contextlib

        try:
            import torch
        except Exception:
            return contextlib.nullcontext()
        cuda_available = bool(getattr(torch.cuda, "is_available", lambda: False)())
        if not cuda_available:
            return contextlib.nullcontext()
        try:
            from torch.nn.attention import SDPBackend, sdpa_kernel
        except Exception as exc:
            raise ModelBackendError(
                "CUDA generation requires torch.nn.attention.sdpa_kernel for the "
                f"fail-closed fused-kernel policy ({KAGGLE_SDPA_KERNEL_POLICY}); "
                f"the installed PyTorch does not provide it: {type(exc).__name__}: {exc}"
            ) from exc
        return sdpa_kernel([SDPBackend.FLASH_ATTENTION, SDPBackend.EFFICIENT_ATTENTION])

    def _generate_sync(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        logger.info("GENERATION_STARTED max_tokens=%d temperature=%s", max_tokens, temperature)
        prompt_tokens: int | None = None
        inputs = None
        input_ids = None
        attention_mask = None
        gen_kwargs = None
        output_ids = None
        generated_ids = None
        try:
            self._ensure_loaded()
            assert self._model is not None
            assert self._tokenizer is not None

            import torch

            chat_prompt = self._format_chat_prompt(prompt)
            inputs = self._tokenizer(chat_prompt, return_tensors="pt")
            input_ids = inputs["input_ids"].to(self._model.device)
            attention_mask = inputs.get("attention_mask")
            if attention_mask is not None:
                attention_mask = attention_mask.to(self._model.device)

            prompt_tokens = input_ids.shape[1]

            gen_kwargs = {
                "input_ids": input_ids,
                "max_new_tokens": max_tokens,
                "do_sample": temperature > 0.0,
                "cache_implementation": KAGGLE_CACHE_IMPLEMENTATION,
            }
            if attention_mask is not None:
                gen_kwargs["attention_mask"] = attention_mask
            if temperature > 0.0:
                gen_kwargs["temperature"] = temperature
                gen_kwargs["top_p"] = 0.95

            with torch.inference_mode(), self._sdpa_kernel_policy_context():
                output_ids = self._model.generate(**gen_kwargs)

            generated_ids = output_ids[0, prompt_tokens:]
            completion_tokens = len(generated_ids)

            # Zero-token output is a measured empty model response, not a backend
            # crash. The regeneration normalizer will classify it as empty and
            # feed that evidence to the bounded repair loop.
            if completion_tokens == 0:
                output_text = ""
                finish_reason = "empty"
            else:
                output_text = self._tokenizer.decode(
                    generated_ids, skip_special_tokens=True
                )
                eos_token_id = self._tokenizer.eos_token_id
                last_token_id = generated_ids[-1].item()
                if last_token_id == eos_token_id:  # noqa: SIM108 - contract requires explicit assignments
                    finish_reason = "eos"
                else:
                    finish_reason = "length"

            logger.info(
                "GENERATION_SUCCEEDED prompt_tokens=%d completion_tokens=%d total_tokens=%d finish_reason=%s",
                prompt_tokens, completion_tokens, prompt_tokens + completion_tokens,
                finish_reason,
            )
            total_tokens = prompt_tokens + completion_tokens
            return LLMResponse(
                text=output_text,
                token_usage=TokenUsage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                ),
                finish_reason=finish_reason,
            )
        except ModelBackendError:
            raise
        except Exception as exc:
            gpu = _gpu_info()
            if exc.__class__.__module__.startswith("torch") and "OutOfMemory" in type(exc).__name__:
                self._log_oom(exc, max_tokens, prompt_tokens)
                raise ModelBackendError(
                    self._format_oom_message(exc, max_tokens, prompt_tokens)
                ) from exc
            logger.error(
                "GENERATION_FAILED exception=%s gpu=%s",
                type(exc).__name__, gpu.get("gpu_name", "unknown"),
            )
            raise ModelBackendError(
                f"Qwen generation failed: {type(exc).__name__}: {exc}"
            ) from exc
        finally:
            # Release every per-call tensor reference before returning a result
            # or before the failure propagates, then reclaim GPU memory. The
            # model and tokenizer stay loaded and reusable.
            del inputs
            del input_ids
            del attention_mask
            del gen_kwargs
            del output_ids
            del generated_ids
            gc.collect()
            _empty_cuda_cache()

    def _format_chat_prompt(self, prompt: str) -> str:
        """Format one user message with the tokenizer's chat template."""
        if self._tokenizer is None:
            raise ModelBackendError("KaggleQwenBackend: tokenizer not loaded")
        apply_chat_template = getattr(self._tokenizer, "apply_chat_template", None)
        if not callable(apply_chat_template):
            raise ModelBackendError(
                "KaggleQwenBackend: tokenizer has no usable chat template. "
                "Use a Qwen chat/instruct tokenizer that provides apply_chat_template."
            )
        try:
            return apply_chat_template(
                [
                    {"role": "system", "content": SYSTEM_TRANSFORMATION_MESSAGE},
                    {"role": "user", "content": prompt},
                ],
                tokenize=False,
                add_generation_prompt=True,
            )
        except Exception as exc:
            raise ModelBackendError(
                f"KaggleQwenBackend: chat template failed: {type(exc).__name__}: {exc}"
            ) from exc

    def _gpu_memory_line(self) -> str:
        """Best-effort per-GPU memory summary for error messages (may be '')."""
        try:
            import torch

            allocated_gib = torch.cuda.memory_allocated(0) / (1024**3)
            reserved_gib = torch.cuda.memory_reserved(0) / (1024**3)
            total_mem = torch.cuda.get_device_properties(0).total_memory
            free_gib = max(0.0, total_mem - torch.cuda.memory_reserved(0)) / (1024**3)
        except Exception:
            return ""
        return (
            f"gpu0_memory allocated_gib={allocated_gib:.2f} "
            f"reserved_gib={reserved_gib:.2f} free_gib={free_gib:.2f}"
        )

    def _format_oom_message(
        self, exc: BaseException, max_tokens: int, prompt_tokens: int | None
    ) -> str:
        """Build the generation OOM message without misattributing the cause.

        Long-prompt OOM is a prompt-prefill attention failure: the completion
        budget is NOT the controlling memory term, so the message must not
        advise reducing it. The original PyTorch exception stays visible and
        chained.
        """
        header = "Qwen generation failed: CUDA out-of-memory."
        attention_line = (
            f"effective_attention_implementation={self.effective_attention_implementation!r} "
            f"(requested={KAGGLE_ATTENTION_IMPLEMENTATION!r}, "
            f"kernel_policy={KAGGLE_SDPA_KERNEL_POLICY!r})"
        )
        memory_line = self._gpu_memory_line()
        prompt_part = (
            str(prompt_tokens) if prompt_tokens is not None else "unknown"
        )
        original = f"Original exception: {type(exc).__name__}: {exc}"
        if prompt_tokens is not None and prompt_tokens >= LONG_PROMPT_PREFILL_OOM_TOKEN_THRESHOLD:
            return (
                f"{header} Prompt-prefill attention allocation exhausted GPU memory: "
                f"prompt_tokens={prompt_part} requested_completion_tokens={max_tokens}; "
                f"{attention_line}; {memory_line}. A prefill OOM with a long prompt is "
                "typically caused by the attention implementation materializing a "
                "quadratic score matrix, not by the completion budget; reducing "
                f"max_completion_tokens will NOT fix it. {original}"
            )
        return (
            f"{header} Reduce max_completion_tokens_per_call (Smoke uses 1024) or "
            f"select a GPU with more VRAM. prompt_tokens={prompt_part} "
            f"requested_completion_tokens={max_tokens}; {attention_line}; {memory_line}. "
            f"{original}"
        )

    def _log_oom(self, exc: BaseException, max_tokens: int, prompt_tokens: int | None) -> None:
        """Log actionable GPU-memory diagnostics for an out-of-memory failure."""
        allocated_gib: float | None = None
        reserved_gib: float | None = None
        free_gib: float | None = None
        try:
            import torch

            allocated_gib = torch.cuda.memory_allocated(0) / (1024**3)
            reserved_gib = torch.cuda.memory_reserved(0) / (1024**3)
            total_mem = torch.cuda.get_device_properties(0).total_memory
            free_gib = max(0.0, total_mem - torch.cuda.memory_reserved(0)) / (1024**3)
        except Exception:
            pass
        logger.error(
            "GENERATION_OOM allocated_gib=%s reserved_gib=%s free_gib=%s "
            "max_tokens=%d prompt_tokens=%s attention_requested=%s "
            "attention_effective=%s sdpa_kernel_policy=%s exception=%s",
            allocated_gib,
            reserved_gib,
            free_gib,
            max_tokens,
            prompt_tokens,
            KAGGLE_ATTENTION_IMPLEMENTATION,
            self.effective_attention_implementation,
            KAGGLE_SDPA_KERNEL_POLICY,
            type(exc).__name__,
        )

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._lazy_import()
        self._load_model()

    def _lazy_import(self) -> None:
        _set_canonical_alloc_conf()
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

        _set_canonical_alloc_conf()
        model_path = self._resolve_model_path()
        logger.info("Loading model from %s", model_path)

        _check_gpu_compatibility()

        checkpoint_config = _read_checkpoint_config(model_path)
        checkpoint_method = _checkpoint_quantization_method(checkpoint_config)

        if (
            self._quantization_mode in ("bnb-int8", "bnb-nf4")
            and checkpoint_method
            and checkpoint_method not in _QUANTIZATION_METHOD_SAFE
        ):
            raise ModelBackendError(
                f"PREQUANTIZED_CHECKPOINT_INCOMPATIBLE: checkpoint quantization={checkpoint_method}, "
                f"requested loader={self._quantization_mode}. "
                "attach the unquantized Qwen2.5-Coder-14B-Instruct checkpoint"
            )

        tokenizer_kwargs = {
            "trust_remote_code": True,
            "local_files_only": True,
        }
        self._tokenizer = AutoTokenizer.from_pretrained(str(model_path), **tokenizer_kwargs)

        load_kwargs = {
            "trust_remote_code": True,
            "local_files_only": True,
            "device_map": "auto",
            # V0.9.22: never rely on the checkpoint/default Transformers choice;
            # the effective attention path must be SDPA (see
            # KAGGLE_ATTENTION_IMPLEMENTATION and _sdpa_kernel_policy_context).
            "attn_implementation": KAGGLE_ATTENTION_IMPLEMENTATION,
        }
        if self._quantization_mode in ("bnb-int8", "bnb-nf4"):
            from transformers import BitsAndBytesConfig

            load_kwargs["low_cpu_mem_usage"] = True

            if self._quantization_mode == "bnb-int8":
                load_kwargs["quantization_config"] = BitsAndBytesConfig(load_in_8bit=True)
            else:
                load_kwargs["quantization_config"] = BitsAndBytesConfig(
                    load_in_4bit=NF4_LOAD_CONFIG["load_in_4bit"],
                    bnb_4bit_quant_type=NF4_LOAD_CONFIG["bnb_4bit_quant_type"],
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=NF4_LOAD_CONFIG["bnb_4bit_use_double_quant"],
                )
        else:
            load_kwargs["torch_dtype"] = torch.float16

        self._model = AutoModelForCausalLM.from_pretrained(str(model_path), **load_kwargs)
        assert self._model is not None
        self._model.eval()
        self._loaded = True

        gpu_info = _gpu_info()
        gpu_name = gpu_info.get("gpu_name", "cpu") if gpu_info.get("available") else "cpu"
        logger.info(
            "MODEL_INITIALIZATION_SUCCEEDED model=%s device_map=auto gpu=%s quantization=%s footprint_bytes=%d",
            self._model_name, gpu_name, self._quantization_mode, self.model_memory_footprint_bytes,
        )

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
