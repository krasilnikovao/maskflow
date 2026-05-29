import json
from collections.abc import Iterable
from importlib import import_module
from pathlib import Path
from typing import Any, cast

from maskflow.nlp.labels import PROVIDER_PRIORITIES, normalize_entity_type
from maskflow.nlp.models import EntityCandidate
from maskflow.nlp.providers.base import NlpProvider


class QwenProvider(NlpProvider):
    name = "qwen"

    def __init__(
        self,
        *,
        model_name: str | None,
        model_path: Path | None,
        auto_download: bool,
        device: str,
        threshold: float,
        max_context_chars: int,
        max_new_tokens: int,
        labels: tuple[str, ...],
    ) -> None:
        self.model_name = model_name
        self.model_path = model_path
        self.auto_download = auto_download
        self.device = device
        self.threshold = threshold
        self.max_context_chars = max_context_chars
        self.max_new_tokens = max_new_tokens
        self.labels = labels
        self.priority = PROVIDER_PRIORITIES[self.name]
        self._pipeline: Any | None = None

    def detect(self, text: str) -> Iterable[EntityCandidate]:
        if not text:
            return []

        clipped_text = text[: self.max_context_chars]
        prompt = _build_prompt(clipped_text, self.labels)
        generator = self._load_pipeline()
        response = generator(
            prompt,
            max_new_tokens=self.max_new_tokens,
            do_sample=False,
            return_full_text=False,
        )
        generated_text = _extract_generated_text(response)
        if not generated_text:
            return []

        return _parse_candidates(
            generated_text=generated_text,
            text=clipped_text,
            threshold=self.threshold,
            priority=self.priority,
        )

    def _load_pipeline(self) -> Any:
        if self._pipeline is not None:
            return self._pipeline

        if self.model_path is None:
            raise ValueError("Qwen model_path is required")

        try:
            transformers_module = import_module("transformers")
        except ImportError as error:
            raise RuntimeError("transformers is required for Qwen provider") from error

        pipeline_factory = cast(Any, transformers_module).pipeline
        self._pipeline = pipeline_factory(
            "text-generation",
            model=str(self.model_path),
            device=_pipeline_device(self.device),
        )
        return self._pipeline


def _pipeline_device(device: str) -> int:
    normalized = device.strip().lower()
    if normalized == "cpu":
        return -1
    if normalized.startswith("cuda"):
        parts = normalized.split(":", maxsplit=1)
        if len(parts) == 2 and parts[1].isdigit():
            return int(parts[1])
        return 0
    raise ValueError("Qwen device must be 'cpu', 'cuda', or 'cuda:N'")


def _build_prompt(text: str, labels: tuple[str, ...]) -> str:
    label_list = ", ".join(labels)
    return (
        "You are a strict named-entity extraction engine for data masking.\n"
        "Return only a JSON array. Do not include markdown or explanations.\n"
        "Each item must have: label, start, end, confidence.\n"
        "Offsets must be Python string offsets into the provided text.\n"
        f"Allowed labels: {label_list}.\n"
        "Text:\n"
        f"{text}"
    )


def _extract_generated_text(response: Any) -> str:
    if not isinstance(response, list) or not response:
        return ""

    first = response[0]
    if not isinstance(first, dict):
        return ""

    generated = first.get("generated_text")
    if isinstance(generated, str):
        return generated

    return ""


def _parse_candidates(
    *,
    generated_text: str,
    text: str,
    threshold: float,
    priority: int,
) -> list[EntityCandidate]:
    payload = _extract_json_array(generated_text)
    if payload is None:
        return []

    candidates: list[EntityCandidate] = []
    for item in payload:
        if not isinstance(item, dict):
            continue

        candidate = _item_to_candidate(
            item=item,
            text=text,
            threshold=threshold,
            priority=priority,
        )
        if candidate is not None:
            candidates.append(candidate)

    return candidates


def _extract_json_array(generated_text: str) -> list[Any] | None:
    for start in range(len(generated_text)):
        if generated_text[start] != "[":
            continue
        for end in range(len(generated_text) - 1, start, -1):
            if generated_text[end] != "]":
                continue
            try:
                payload = json.loads(generated_text[start : end + 1])
            except json.JSONDecodeError:
                continue
            if isinstance(payload, list):
                return payload
    return None


def _item_to_candidate(
    *,
    item: dict[Any, Any],
    text: str,
    threshold: float,
    priority: int,
) -> EntityCandidate | None:
    label = item.get("label")
    start = item.get("start")
    end = item.get("end")
    confidence = item.get("confidence")

    if (
        not isinstance(label, str)
        or not isinstance(start, int)
        or not isinstance(end, int)
    ):
        return None
    if not isinstance(confidence, (int, float)):
        return None

    confidence_float = float(confidence)
    if confidence_float < threshold:
        return None
    if start < 0 or end <= start or end > len(text):
        return None

    return EntityCandidate(
        entity_type=normalize_entity_type(label),
        start=start,
        end=end,
        value=text[start:end],
        source=QwenProvider.name,
        confidence=confidence_float,
        priority=priority,
    )
