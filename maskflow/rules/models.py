from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

_StrictModel = ConfigDict(extra="forbid")

FieldAction = Literal["mask", "remove", "replace"]


class PipelineConfig(BaseModel):
    model_config = _StrictModel
    deterministic_secret: str = Field(min_length=1)


class RuleConfig(BaseModel):
    model_config = _StrictModel
    enabled: bool = True
    # mode is a free string: business validation is delegated to the factory,
    # which knows which modes are actually supported.
    mode: str = "hmac"
    prefix: str


class FieldRuleConfig(BaseModel):
    model_config = _StrictModel
    enabled: bool = True
    action: FieldAction = "mask"
    replacement: str | None = None


class RuntimeLimitsConfig(BaseModel):
    model_config = _StrictModel
    regex_timeout_seconds: float = Field(
        default=1.0,
        gt=0,
        le=10,
    )
    file_timeout_seconds: int | None = Field(
        default=None,
        gt=0,
    )
    max_workers: int = Field(
        default=1,
        gt=0,
        le=32,
        description="Safety cap on parallel processes",
    )


class CacheConfig(BaseModel):
    model_config = _StrictModel
    enabled: bool = False
    path: str = ".maskflow/entity-cache.json"


class ReversibleMappingConfig(BaseModel):
    model_config = _StrictModel
    enabled: bool = False
    path: str = ".maskflow/reversible-map.bin"
    encryption_key_env: str = "MASKFLOW_REVERSIBLE_KEY"


class AppConfig(BaseModel):
    model_config = _StrictModel
    pipeline: PipelineConfig
    rules: dict[str, RuleConfig]
    field_rules: dict[str, FieldRuleConfig] = Field(default_factory=dict)
    runtime_limits: RuntimeLimitsConfig = Field(default_factory=RuntimeLimitsConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    reversible_mapping: ReversibleMappingConfig = Field(
        default_factory=ReversibleMappingConfig,
    )
