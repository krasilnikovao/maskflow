from pathlib import Path
from types import SimpleNamespace

import pytest
from pytest import MonkeyPatch

from maskflow.nlp.providers import gliner as gliner_provider_module
from maskflow.nlp.providers.gliner import GlinerProvider


class FakeGlinerModel:
    def __init__(self) -> None:
        self.device: str | None = None

    def to(self, device: str) -> None:
        self.device = device

    def predict_entities(
        self,
        text: str,
        labels: list[str],
        threshold: float,
    ) -> list[dict[str, object]]:
        assert labels == ["person", "organization"]
        assert threshold == 0.7
        return [
            {
                "start": text.index("Иван Петров"),
                "end": text.index("Иван Петров") + len("Иван Петров"),
                "label": "person",
                "score": 0.91,
            },
            {
                "start": text.index("ООО Ромашка"),
                "end": text.index("ООО Ромашка") + len("ООО Ромашка"),
                "label": "organization",
                "score": 0.88,
            },
        ]


class FakeGlinerClass:
    loaded_path: str | None = None
    loaded_model_dir: str | None = None
    loaded_local_files_only: bool | None = None

    @classmethod
    def from_pretrained(
        cls,
        model_path: str,
        model_dir: str | None = None,
        local_files_only: bool = False,
    ) -> FakeGlinerModel:
        cls.loaded_path = model_path
        cls.loaded_model_dir = model_dir
        cls.loaded_local_files_only = local_files_only
        return FakeGlinerModel()


class FakeBusinessLabelGlinerModel:
    def predict_entities(
        self,
        text: str,
        labels: list[str],
        threshold: float,
    ) -> list[dict[str, object]]:
        assert labels == ["full name", "bank"]
        assert threshold == 0.5
        return [
            {
                "start": text.index("Иван Петров"),
                "end": text.index("Иван Петров") + len("Иван Петров"),
                "label": "full name",
                "score": 0.91,
            },
            {
                "start": text.index("Банк Ромашка"),
                "end": text.index("Банк Ромашка") + len("Банк Ромашка"),
                "label": "bank",
                "score": 0.88,
            },
        ]


class FakeBusinessLabelGlinerClass:
    @classmethod
    def from_pretrained(
        cls,
        _model_path: str,
        model_dir: str | None = None,
        local_files_only: bool = False,
    ) -> FakeBusinessLabelGlinerModel:
        return FakeBusinessLabelGlinerModel()


class FakeLegacyGlinerClass:
    loaded_path: str | None = None
    loaded_local_files_only: bool | None = None

    @classmethod
    def from_pretrained(
        cls,
        model_path: str,
        local_files_only: bool = False,
    ) -> FakeGlinerModel:
        cls.loaded_path = model_path
        cls.loaded_local_files_only = local_files_only
        return FakeGlinerModel()


def test_gliner_provider_converts_entities_to_candidates(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    fake_module = SimpleNamespace(GLiNER=FakeGlinerClass)
    monkeypatch.setattr(
        gliner_provider_module,
        "import_module",
        lambda _name: fake_module,
    )

    provider = GlinerProvider(
        model_name="example/gliner",
        model_path=tmp_path / "model",
        auto_download=False,
        labels=("person", "organization"),
        device="cpu",
        threshold=0.7,
        batch_size=8,
    )

    candidates = list(provider.detect("Клиент Иван Петров работает в ООО Ромашка"))

    assert FakeGlinerClass.loaded_path == "example/gliner"
    assert FakeGlinerClass.loaded_model_dir == str(tmp_path / "model")
    assert FakeGlinerClass.loaded_local_files_only is False
    assert [candidate.entity_type for candidate in candidates] == [
        "person",
        "organization",
    ]
    assert candidates[0].value == "Иван Петров"
    assert candidates[0].confidence == 0.91


def test_gliner_provider_normalizes_business_labels(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    fake_module = SimpleNamespace(GLiNER=FakeBusinessLabelGlinerClass)
    monkeypatch.setattr(
        gliner_provider_module,
        "import_module",
        lambda _name: fake_module,
    )

    provider = GlinerProvider(
        model_name="example/gliner",
        model_path=tmp_path / "model",
        auto_download=False,
        labels=("full name", "bank"),
        device="cpu",
        threshold=0.5,
        batch_size=8,
    )

    candidates = list(provider.detect("Клиент Иван Петров обслуживается в Банк Ромашка"))

    assert [candidate.entity_type for candidate in candidates] == [
        "person",
        "organization",
    ]


def test_gliner_provider_supports_legacy_local_path_loading(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    fake_module = SimpleNamespace(GLiNER=FakeLegacyGlinerClass)
    monkeypatch.setattr(
        gliner_provider_module,
        "import_module",
        lambda _name: fake_module,
    )

    provider = GlinerProvider(
        model_name="example/gliner",
        model_path=tmp_path / "model",
        auto_download=False,
        labels=("person", "organization"),
        device="cpu",
        threshold=0.7,
        batch_size=8,
    )

    list(provider.detect("Клиент Иван Петров работает в ООО Ромашка"))

    assert FakeLegacyGlinerClass.loaded_path == str(tmp_path / "model")
    assert FakeLegacyGlinerClass.loaded_local_files_only is False


def test_gliner_provider_requires_dependency(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    def fail_import(_name: str) -> object:
        raise ImportError

    monkeypatch.setattr(gliner_provider_module, "import_module", fail_import)

    provider = GlinerProvider(
        model_name="example/gliner",
        model_path=tmp_path / "model",
        auto_download=False,
        labels=("person",),
        device="cpu",
        threshold=0.5,
        batch_size=8,
    )

    with pytest.raises(RuntimeError, match="gliner is required"):
        list(provider.detect("Иван"))
