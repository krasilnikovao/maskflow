from collections.abc import Generator

import pytest

from maskflow.runtime.settings import get_settings

_NLP_ENV_NAMES = (
    "MASKFLOW_NLP_ENABLED",
    "MASKFLOW_NLP_AUTO_DOWNLOAD",
    "MASKFLOW_GLINER_ENABLED",
    "MASKFLOW_GLINER_MODEL",
    "MASKFLOW_GLINER_MODEL_PATH",
    "MASKFLOW_GLINER_DEVICE",
    "MASKFLOW_SPACY_ENABLED",
    "MASKFLOW_SPACY_MODEL",
    "MASKFLOW_SPACY_MODEL_PATH",
    "MASKFLOW_NATASHA_ENABLED",
    "MASKFLOW_QWEN_ENABLED",
    "MASKFLOW_QWEN_MODEL",
    "MASKFLOW_QWEN_MODEL_PATH",
    "MASKFLOW_QWEN_DEVICE",
)


@pytest.fixture(autouse=True)
def clear_host_nlp_env(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    for name in _NLP_ENV_NAMES:
        monkeypatch.delenv(name, raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
