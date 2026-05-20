import os
from pathlib import Path
from typing import Any

import yaml

from maskflow.rules.models import AppConfig

INVALID_DEFAULT_SECRETS = {"", "CHANGE_ME", "change_me", "changeme"}


class RulesLoader:
    @staticmethod
    def load(path: str | Path) -> AppConfig:
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

        if config.pipeline.deterministic_secret in INVALID_DEFAULT_SECRETS:
            raise ValueError(
                "pipeline.deterministic_secret is not configured. "
                "Set it in YAML or via MASKFLOW_SECRET environment variable."
            )

        return config
