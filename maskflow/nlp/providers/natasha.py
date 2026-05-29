from collections.abc import Iterable
from importlib import import_module
from typing import Any, cast

from maskflow.nlp.labels import PROVIDER_PRIORITIES, normalize_entity_type
from maskflow.nlp.models import EntityCandidate
from maskflow.nlp.providers.base import NlpProvider


class NatashaProvider(NlpProvider):
    name = "natasha"

    def __init__(self) -> None:
        self._segmenter: Any | None = None
        self._morph_vocab: Any | None = None
        self._ner_tagger: Any | None = None
        self._doc_class: Any | None = None

    def detect(self, text: str) -> Iterable[EntityCandidate]:
        if not text:
            return []

        self._ensure_loaded()
        doc_class = self._doc_class
        if doc_class is None:
            raise RuntimeError("Natasha provider was not initialized")

        doc = doc_class(text)
        doc.segment(self._segmenter)
        doc.tag_ner(self._ner_tagger)

        for span in doc.spans:
            span.normalize(self._morph_vocab)

        candidates: list[EntityCandidate] = []
        for span in doc.spans:
            candidate = _span_to_candidate(span, text)
            if candidate is not None:
                candidates.append(candidate)

        return candidates

    def _ensure_loaded(self) -> None:
        if self._doc_class is not None:
            return

        try:
            natasha_module = import_module("natasha")
        except ImportError as error:
            raise RuntimeError("natasha is required for Natasha provider") from error

        module = cast(Any, natasha_module)
        self._segmenter = module.Segmenter()
        self._morph_vocab = module.MorphVocab()
        embedding = module.NewsEmbedding()
        self._ner_tagger = module.NewsNERTagger(embedding)
        self._doc_class = module.Doc


def _span_to_candidate(span: Any, text: str) -> EntityCandidate | None:
    start = getattr(span, "start", None)
    stop = getattr(span, "stop", None)
    span_type = getattr(span, "type", None)

    if (
        not isinstance(start, int)
        or not isinstance(stop, int)
        or not isinstance(span_type, str)
    ):
        return None

    if start < 0 or stop <= start or stop > len(text):
        return None

    return EntityCandidate(
        entity_type=normalize_entity_type(span_type),
        start=start,
        end=stop,
        value=text[start:stop],
        source=NatashaProvider.name,
        confidence=None,
        priority=PROVIDER_PRIORITIES[NatashaProvider.name],
    )
