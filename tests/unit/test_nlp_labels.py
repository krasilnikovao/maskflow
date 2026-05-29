from maskflow.nlp.labels import PROVIDER_PRIORITIES


def test_provider_priorities_include_qwen() -> None:
    assert PROVIDER_PRIORITIES == {
        "spacy": 30,
        "natasha": 20,
        "qwen": 15,
        "gliner": 10,
    }
