from collections.abc import Iterable
from importlib import import_module
from pathlib import Path
from typing import Any, cast

from maskflow.nlp.labels import PROVIDER_PRIORITIES, normalize_entity_type
from maskflow.nlp.models import EntityCandidate
from maskflow.nlp.providers.base import NlpProvider


class GlinerProvider(NlpProvider):
    name = "gliner"

    def __init__(
        self,
        *,
        model_name: str,
        model_path: Path | None,
        auto_download: bool,
        labels: tuple[str, ...],
        device: str,
        threshold: float,
        batch_size: int,
    ) -> None:
        self.model_name = model_name
        self.model_path = model_path
        self.auto_download = auto_download
        self.labels = labels
        self.device = device
        self.threshold = threshold
        self.batch_size = batch_size
        self._model: Any | None = None

    def detect(self, text: str) -> Iterable[EntityCandidate]:
        if not text:
            return []

        model = self._load_model()
        entities = model.predict_entities(
            text,
            list(self.labels),
            threshold=self.threshold,
        )

        candidates: list[EntityCandidate] = []
        for entity in entities:
            candidate = _entity_to_candidate(entity, text)
            if candidate is not None:
                candidates.append(candidate)

        return candidates

    def _load_model(self) -> Any:
        if self._model is not None:
            return self._model

        if self.model_path is None:
            raise ValueError("GLiNER model_path is required")

        try:
            gliner_module = import_module("gliner")
        except ImportError as error:
            raise RuntimeError("gliner is required for GLiNER provider") from error

        gliner_class = cast(Any, gliner_module).GLiNER
        self._model = gliner_class.from_pretrained(str(self.model_path))

        to_method = getattr(self._model, "to", None)
        if callable(to_method):
            to_method(self.device)

        return self._model


def _entity_to_candidate(
    entity: Any,
    text: str,
) -> EntityCandidate | None:
    if not isinstance(entity, dict):
        return None

    start = entity.get("start")
    end = entity.get("end")
    label = entity.get("label")

    if (
        not isinstance(start, int)
        or not isinstance(end, int)
        or not isinstance(label, str)
    ):
        return None

    if start < 0 or end <= start or end > len(text):
        return None

    score = entity.get("score")
    confidence = float(score) if isinstance(score, (int, float)) else None

    return EntityCandidate(
        entity_type=normalize_entity_type(label),
        start=start,
        end=end,
        value=text[start:end],
        source=GlinerProvider.name,
        confidence=confidence,
        priority=PROVIDER_PRIORITIES[GlinerProvider.name],
    )
