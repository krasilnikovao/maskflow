from collections.abc import Iterable
from importlib import import_module
from typing import Any, cast

from maskflow.nlp.labels import PROVIDER_PRIORITIES, normalize_entity_type
from maskflow.nlp.models import EntityCandidate
from maskflow.nlp.providers.base import NlpProvider


class SpacyProvider(NlpProvider):
    name = "spacy"

    def __init__(
        self,
        *,
        model_name: str,
        model_path: str | None,
        auto_download: bool,
        batch_size: int,
    ) -> None:
        self.model_name = model_name
        self.model_path = model_path
        self.auto_download = auto_download
        self.batch_size = batch_size
        self._nlp: Any | None = None

    def detect(self, text: str) -> Iterable[EntityCandidate]:
        if not text:
            return []

        nlp = self._load_pipeline()
        doc = nlp(text)

        candidates: list[EntityCandidate] = []
        for entity in doc.ents:
            candidate = _entity_to_candidate(entity, text)
            if candidate is not None:
                candidates.append(candidate)

        return candidates

    def _load_pipeline(self) -> Any:
        if self._nlp is not None:
            return self._nlp

        try:
            spacy_module = import_module("spacy")
        except ImportError as error:
            raise RuntimeError("spaCy is required for spaCy provider") from error

        load_target = self.model_path or self.model_name
        self._nlp = cast(Any, spacy_module).load(load_target)
        return self._nlp


def _entity_to_candidate(entity: Any, text: str) -> EntityCandidate | None:
    start = getattr(entity, "start_char", None)
    end = getattr(entity, "end_char", None)
    label = getattr(entity, "label_", None)

    if (
        not isinstance(start, int)
        or not isinstance(end, int)
        or not isinstance(label, str)
    ):
        return None

    if start < 0 or end <= start or end > len(text):
        return None

    return EntityCandidate(
        entity_type=normalize_entity_type(label),
        start=start,
        end=end,
        value=text[start:end],
        source=SpacyProvider.name,
        confidence=None,
        priority=PROVIDER_PRIORITIES[SpacyProvider.name],
    )
