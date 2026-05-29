from pathlib import Path
from types import SimpleNamespace

import pytest
from pytest import MonkeyPatch

from maskflow.nlp.providers import qwen as qwen_provider_module
from maskflow.nlp.providers.qwen import QwenProvider


class FakeQwenPipeline:
    def __call__(
        self,
        prompt: str,
        max_new_tokens: int,
        do_sample: bool,
        return_full_text: bool,
    ) -> list[dict[str, str]]:
        assert "Allowed labels: person, organization." in prompt
        assert max_new_tokens == 128
        assert do_sample is False
        assert return_full_text is False
        text_start = prompt.index("Иван Петров")
        assert text_start > 0
        return [
            {
                "generated_text": (
                    '[{"label":"person","start":7,"end":18,"confidence":0.91},'
                    '{"label":"organization","start":30,"end":41,"confidence":0.4}]'
                )
            }
        ]


class FakeTransformersModule:
    loaded_model: str | None = None
    loaded_device: int | None = None

    @classmethod
    def pipeline(cls, task: str, model: str, device: int) -> FakeQwenPipeline:
        assert task == "text-generation"
        cls.loaded_model = model
        cls.loaded_device = device
        return FakeQwenPipeline()


def test_qwen_provider_converts_json_response_to_candidates(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    fake_module = SimpleNamespace(pipeline=FakeTransformersModule.pipeline)
    monkeypatch.setattr(
        qwen_provider_module,
        "import_module",
        lambda _name: fake_module,
    )

    provider = QwenProvider(
        model_name="Qwen/example",
        model_path=tmp_path / "qwen",
        auto_download=False,
        device="cpu",
        threshold=0.5,
        max_context_chars=4000,
        max_new_tokens=128,
        labels=("person", "organization"),
    )

    candidates = list(
        provider.detect("Клиент Иван Петров работает в ООО Ромашка")
    )

    assert FakeTransformersModule.loaded_model == str(tmp_path / "qwen")
    assert FakeTransformersModule.loaded_device == -1
    assert len(candidates) == 1
    assert candidates[0].entity_type == "person"
    assert candidates[0].value == "Иван Петров"
    assert candidates[0].source == "qwen"
    assert candidates[0].priority == 15


def test_qwen_provider_requires_dependency(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    def fail_import(_name: str) -> object:
        raise ImportError

    monkeypatch.setattr(qwen_provider_module, "import_module", fail_import)

    provider = QwenProvider(
        model_name="Qwen/example",
        model_path=tmp_path / "qwen",
        auto_download=False,
        device="cpu",
        threshold=0.5,
        max_context_chars=4000,
        max_new_tokens=128,
        labels=("person",),
    )

    with pytest.raises(RuntimeError, match="transformers is required"):
        list(provider.detect("Иван"))
