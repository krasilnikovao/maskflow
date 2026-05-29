from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MaskFlowSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MASKFLOW_",
        env_file=".env",
        extra="ignore",
    )

    data_dir: Path = Field(default=Path("data"))
    default_config: Path = Field(default=Path("configs/default.yaml"))
    log_level: str = Field(default="INFO")
    api_host: str = Field(default="127.0.0.1")
    api_port: int = Field(default=3100, gt=0, le=65535)

    # NLP model download defaults. Auto-download is disabled by default to
    # preserve offline behavior. Model files live under {data_dir}/models.
    nlp_enabled: bool | None = Field(default=None)
    nlp_auto_download: bool = Field(default=False)
    gliner_enabled: bool | None = Field(default=None)
    gliner_model: str = Field(default="urchade/gliner_multi-v2.1")
    gliner_model_path: str | None = Field(default=None)
    gliner_device: str | None = Field(default=None)
    spacy_enabled: bool | None = Field(default=None)
    spacy_model: str = Field(default="ru_core_news_lg")
    spacy_model_path: str | None = Field(default=None)
    natasha_enabled: bool | None = Field(default=None)
    qwen_enabled: bool | None = Field(default=None)
    qwen_model: str = Field(default="Qwen/Qwen2.5-Coder-7B-Instruct")
    qwen_model_path: str | None = Field(default=None)
    qwen_device: str | None = Field(default=None)


@lru_cache(maxsize=1)
def get_settings() -> MaskFlowSettings:
    return MaskFlowSettings()
