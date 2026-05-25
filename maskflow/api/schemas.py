from pathlib import Path

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    data_dir: Path


class RuleInfo(BaseModel):
    name: str
    detector: str


class ConfigInfo(BaseModel):
    name: str
    path: Path


class MaskTextRequest(BaseModel):
    text: str = Field(min_length=1)
    config_path: Path | None = None
    plugins_dir: Path | None = None


class MaskTextResponse(BaseModel):
    masked_text: str
    matches_found: int
    matches_applied: int
    matches_skipped: int
    detector_counts: dict[str, int]
    detector_timings_ms: dict[str, int]
