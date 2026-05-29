from maskflow.nlp.models import EntityCandidate
from maskflow.nlp.resolver import NlpResolver


def test_nlp_resolver_keeps_non_overlapping_candidates() -> None:
    candidates = [
        EntityCandidate(
            entity_type="person",
            start=0,
            end=11,
            value="Иван Петров",
            source="gliner",
            confidence=0.8,
        ),
        EntityCandidate(
            entity_type="organization",
            start=23,
            end=34,
            value="ООО Ромашка",
            source="spacy",
            confidence=0.9,
        ),
    ]

    resolved = NlpResolver().resolve(candidates)

    assert [entity.entity_type for entity in resolved] == ["person", "organization"]


def test_nlp_resolver_prefers_higher_priority_on_same_start() -> None:
    candidates = [
        EntityCandidate(
            entity_type="organization",
            start=0,
            end=7,
            value="Ромашка",
            source="gliner",
            confidence=0.9,
            priority=10,
        ),
        EntityCandidate(
            entity_type="organization",
            start=0,
            end=11,
            value="ООО Ромашка",
            source="spacy",
            confidence=0.7,
            priority=20,
        ),
    ]

    resolved = NlpResolver().resolve(candidates)

    assert len(resolved) == 1
    assert resolved[0].value == "ООО Ромашка"
    assert resolved[0].sources == ("gliner", "spacy")
    assert resolved[0].confidence == 0.9


def test_nlp_resolver_filters_low_confidence_candidates() -> None:
    candidates = [
        EntityCandidate(
            entity_type="person",
            start=0,
            end=4,
            value="Иван",
            source="gliner",
            confidence=0.4,
        ),
        EntityCandidate(
            entity_type="person",
            start=5,
            end=11,
            value="Петров",
            source="spacy",
            confidence=0.8,
        ),
    ]

    resolved = NlpResolver(min_confidence=0.5).resolve(candidates)

    assert len(resolved) == 1
    assert resolved[0].value == "Петров"


def test_nlp_resolver_merges_same_type_overlapping_sources() -> None:
    candidates = [
        EntityCandidate(
            entity_type="person",
            start=0,
            end=4,
            value="Иван",
            source="gliner",
            confidence=0.8,
            priority=10,
        ),
        EntityCandidate(
            entity_type="person",
            start=0,
            end=11,
            value="Иван Петров",
            source="natasha",
            confidence=None,
            priority=20,
        ),
    ]

    resolved = NlpResolver().resolve(candidates)

    assert len(resolved) == 1
    assert resolved[0].value == "Иван Петров"
    assert resolved[0].sources == ("gliner", "natasha")
    assert resolved[0].confidence == 0.8


def test_nlp_resolver_prefers_higher_priority_between_entity_types() -> None:
    candidates = [
        EntityCandidate(
            entity_type="location",
            start=0,
            end=6,
            value="Москва",
            source="gliner",
            confidence=0.95,
            priority=10,
        ),
        EntityCandidate(
            entity_type="organization",
            start=0,
            end=10,
            value="Москва ООО",
            source="spacy",
            confidence=0.6,
            priority=30,
        ),
    ]

    resolved = NlpResolver().resolve(candidates)

    assert len(resolved) == 1
    assert resolved[0].entity_type == "organization"
    assert resolved[0].value == "Москва ООО"
    assert resolved[0].sources == ("spacy",)
