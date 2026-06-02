from maskflow.nlp.labels import (
    DEFAULT_DETECTION_LABELS,
    DEFAULT_ENTITY_TYPES,
    PROVIDER_PRIORITIES,
    normalize_entity_type,
)


def test_provider_priorities_include_qwen() -> None:
    assert PROVIDER_PRIORITIES == {
        "spacy": 30,
        "natasha": 20,
        "qwen": 15,
        "gliner": 10,
    }


def test_detection_labels_are_wider_than_runtime_entity_types() -> None:
    assert DEFAULT_ENTITY_TYPES == (
        "person",
        "organization",
        "location",
        "address",
    )
    assert DEFAULT_DETECTION_LABELS == (
        "person",
        "full name",
        "organization",
        "company",
        "bank",
        "legal entity",
        "individual entrepreneur",
        "location",
        "address",
    )


def test_business_label_aliases_normalize_to_existing_entity_types() -> None:
    assert normalize_entity_type("full name") == "person"
    assert normalize_entity_type("company") == "organization"
    assert normalize_entity_type("bank") == "organization"
    assert normalize_entity_type("bank branch") == "organization"
    assert normalize_entity_type("legal entity") == "organization"
    assert normalize_entity_type("individual entrepreneur") == "organization"
