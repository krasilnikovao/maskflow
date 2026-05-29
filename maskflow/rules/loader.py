import os
from pathlib import Path
from typing import Any

import yaml

from maskflow.rules.models import AppConfig

INVALID_DEFAULT_SECRETS = {
    "",
    "CHANGE_ME",
    "change_me",
    "changeme",
    # Дефолтное значение из configs/default.yaml — явно не настроено
    "set-via-MASKFLOW_SECRET",
}

_TRUE_ENV_VALUES = {"1", "true", "yes", "on"}
_FALSE_ENV_VALUES = {"0", "false", "no", "off"}


class RulesLoader:
    @staticmethod
    def load(path: str | Path, validate_secret: bool = True) -> AppConfig:
        config_path = Path(path)

        if not config_path.exists():
            raise FileNotFoundError(config_path)

        if not config_path.is_file():
            raise ValueError(f"Config path is not a file: {config_path}")

        with config_path.open(encoding="utf-8") as file:
            data: Any = yaml.safe_load(file)

        if not isinstance(data, dict):
            raise ValueError("Config root must be a YAML object")

        config = AppConfig.model_validate(data)

        # Поддержка переопределения секрета из ENV (рекомендованный способ).
        env_secret = os.getenv("MASKFLOW_SECRET")
        if env_secret:
            config = config.model_copy(
                update={
                    "pipeline": config.pipeline.model_copy(
                        update={"deterministic_secret": env_secret}
                    )
                }
            )

        config = _apply_nlp_env_overrides(config)

        if (
            validate_secret
            and config.pipeline.deterministic_secret in INVALID_DEFAULT_SECRETS
        ):
            raise ValueError(
                "pipeline.deterministic_secret is not configured. "
                "Set it in YAML or via MASKFLOW_SECRET environment variable."
            )

        return config


def _apply_nlp_env_overrides(config: AppConfig) -> AppConfig:
    nlp = config.nlp

    nlp_updates: dict[str, Any] = {}
    nlp_enabled = _parse_optional_bool_env("MASKFLOW_NLP_ENABLED")
    if nlp_enabled is not None:
        nlp_updates["enabled"] = nlp_enabled
    nlp_auto_download = _parse_optional_bool_env("MASKFLOW_NLP_AUTO_DOWNLOAD")
    if nlp_auto_download is not None:
        nlp_updates["auto_download"] = nlp_auto_download
    if nlp_updates:
        nlp = nlp.model_copy(update=nlp_updates)

    providers = nlp.providers

    gliner_updates: dict[str, Any] = {}
    gliner_enabled = _parse_optional_bool_env("MASKFLOW_GLINER_ENABLED")
    if gliner_enabled is not None:
        gliner_updates["enabled"] = gliner_enabled
    _apply_optional_env(gliner_updates, "model_name", "MASKFLOW_GLINER_MODEL")
    _apply_optional_env(gliner_updates, "model_path", "MASKFLOW_GLINER_MODEL_PATH")
    _apply_optional_env(gliner_updates, "device", "MASKFLOW_GLINER_DEVICE")

    spacy_updates: dict[str, Any] = {}
    spacy_enabled = _parse_optional_bool_env("MASKFLOW_SPACY_ENABLED")
    if spacy_enabled is not None:
        spacy_updates["enabled"] = spacy_enabled
    _apply_optional_env(spacy_updates, "model_name", "MASKFLOW_SPACY_MODEL")
    _apply_optional_env(spacy_updates, "model_path", "MASKFLOW_SPACY_MODEL_PATH")

    natasha_updates: dict[str, Any] = {}
    natasha_enabled = _parse_optional_bool_env("MASKFLOW_NATASHA_ENABLED")
    if natasha_enabled is not None:
        natasha_updates["enabled"] = natasha_enabled

    qwen_updates: dict[str, Any] = {}
    qwen_enabled = _parse_optional_bool_env("MASKFLOW_QWEN_ENABLED")
    if qwen_enabled is not None:
        qwen_updates["enabled"] = qwen_enabled
    _apply_optional_env(qwen_updates, "model_name", "MASKFLOW_QWEN_MODEL")
    _apply_optional_env(qwen_updates, "model_path", "MASKFLOW_QWEN_MODEL_PATH")
    _apply_optional_env(qwen_updates, "device", "MASKFLOW_QWEN_DEVICE")

    providers = providers.model_copy(
        update={
            "gliner": providers.gliner.model_copy(update=gliner_updates),
            "spacy": providers.spacy.model_copy(update=spacy_updates),
            "natasha": providers.natasha.model_copy(update=natasha_updates),
            "qwen": providers.qwen.model_copy(update=qwen_updates),
        }
    )

    nlp = nlp.model_copy(update={"providers": providers})
    return config.model_copy(update={"nlp": nlp})


def _apply_optional_env(updates: dict[str, Any], field_name: str, env_name: str) -> None:
    value = os.getenv(env_name)
    if value:
        updates[field_name] = value


def _parse_optional_bool_env(name: str) -> bool | None:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value == "":
        return None

    value = raw_value.strip().lower()
    if value in _TRUE_ENV_VALUES:
        return True
    if value in _FALSE_ENV_VALUES:
        return False

    raise ValueError(
        f"{name} must be one of: {sorted(_TRUE_ENV_VALUES | _FALSE_ENV_VALUES)}"
    )
