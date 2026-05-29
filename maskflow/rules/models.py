from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from maskflow.nlp.labels import DEFAULT_ENTITY_TYPES

_StrictModel = ConfigDict(extra="forbid")

FieldAction = Literal["mask", "remove", "replace"]
NlpProviderName = Literal["gliner", "spacy", "natasha", "qwen"]

# All supported masking modes. Adding a new mode here requires a corresponding
# implementation in maskflow/core/factory.py.
MaskingMode = Literal["hmac", "partial", "preserve_format", "redact"]


class PipelineConfig(BaseModel):
    model_config = _StrictModel
    deterministic_secret: str = Field(min_length=1)


class GlinerProviderConfig(BaseModel):
    model_config = _StrictModel
    enabled: bool = False
    # Hugging Face model id used when auto_download is enabled.
    model_name: str = "urchade/gliner_multi-v2.1"
    # Absolute path or path relative to data/models.
    model_path: str | None = None
    # None means inherit nlp.auto_download.
    auto_download: bool | None = None
    labels: tuple[str, ...] = DEFAULT_ENTITY_TYPES
    device: str = "cpu"
    threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    batch_size: int = Field(default=16, gt=0, le=256)


class SpacyProviderConfig(BaseModel):
    model_config = _StrictModel
    enabled: bool = False
    # spaCy package name used when auto_download is enabled.
    model_name: str = "ru_core_news_lg"
    # Absolute path, installed package name, or path relative to data/models.
    model_path: str | None = None
    # None means inherit nlp.auto_download.
    auto_download: bool | None = None
    batch_size: int = Field(default=32, gt=0, le=512)


class NatashaProviderConfig(BaseModel):
    model_config = _StrictModel
    enabled: bool = False


class QwenProviderConfig(BaseModel):
    model_config = _StrictModel
    enabled: bool = False
    # Hugging Face model id used when auto_download is enabled.
    model_name: str = "Qwen/Qwen2.5-Coder-7B-Instruct"
    # Absolute path or path relative to data/models.
    model_path: str | None = None
    # None means inherit nlp.auto_download.
    auto_download: bool | None = None
    labels: tuple[str, ...] = DEFAULT_ENTITY_TYPES
    device: str = "cpu"
    threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    max_context_chars: int = Field(default=4000, gt=0, le=64000)
    max_new_tokens: int = Field(default=512, gt=0, le=4096)


class NlpProvidersConfig(BaseModel):
    model_config = _StrictModel
    gliner: GlinerProviderConfig = Field(default_factory=GlinerProviderConfig)
    spacy: SpacyProviderConfig = Field(default_factory=SpacyProviderConfig)
    natasha: NatashaProviderConfig = Field(default_factory=NatashaProviderConfig)
    qwen: QwenProviderConfig = Field(default_factory=QwenProviderConfig)


class NlpConfig(BaseModel):
    model_config = _StrictModel
    enabled: bool = False
    # Disabled by default to preserve fully offline behavior unless explicitly allowed.
    auto_download: bool = False
    min_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    provider_order: tuple[NlpProviderName, ...] = (
        "gliner",
        "spacy",
        "natasha",
        "qwen",
    )
    providers: NlpProvidersConfig = Field(default_factory=NlpProvidersConfig)


class RuleConfig(BaseModel):
    model_config = _StrictModel
    enabled: bool = True
    mode: MaskingMode = "hmac"
    # prefix defaults to "" — factory derives it from the rule name when empty.
    prefix: str = ""


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
    nlp: NlpConfig = Field(default_factory=NlpConfig)
    rules: dict[str, RuleConfig]
    field_rules: dict[str, FieldRuleConfig] = Field(default_factory=dict)
    runtime_limits: RuntimeLimitsConfig = Field(default_factory=RuntimeLimitsConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    reversible_mapping: ReversibleMappingConfig = Field(
        default_factory=ReversibleMappingConfig,
    )
