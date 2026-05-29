from pathlib import Path

from pytest import MonkeyPatch

from maskflow.nlp.status import collect_nlp_model_status
from maskflow.rules.models import (
    GlinerProviderConfig,
    NlpConfig,
    NlpProvidersConfig,
)
from maskflow.runtime.settings import get_settings


def test_collect_nlp_model_status_reports_default_paths(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setenv("MASKFLOW_DATA_DIR", str(tmp_path / "data"))
    get_settings.cache_clear()

    try:
        statuses = collect_nlp_model_status(NlpConfig())
    finally:
        get_settings.cache_clear()

    by_provider = {status.provider: status for status in statuses}

    assert by_provider["gliner"].model_path == (
        tmp_path / "data" / "models" / "huggingface" / "urchade__gliner_multi-v2.1"
    )
    assert by_provider["gliner"].available is False
    assert by_provider["qwen"].model_path == (
        tmp_path
        / "data"
        / "models"
        / "huggingface"
        / "Qwen__Qwen2.5-Coder-7B-Instruct"
    )


def test_collect_nlp_model_status_reports_existing_explicit_path(
    tmp_path: Path,
) -> None:
    model_path = tmp_path / "gliner"
    model_path.mkdir()
    (model_path / "config.json").write_text("{}", encoding="utf-8")

    statuses = collect_nlp_model_status(
        NlpConfig(
            providers=NlpProvidersConfig(
                gliner=GlinerProviderConfig(
                    enabled=True,
                    model_path=str(model_path),
                )
            )
        )
    )

    gliner_status = {status.provider: status for status in statuses}["gliner"]

    assert gliner_status.enabled is True
    assert gliner_status.model_path == model_path
    assert gliner_status.available is True
