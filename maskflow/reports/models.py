from dataclasses import dataclass, field
from pathlib import Path

from maskflow.audit.models import AuditTrail


@dataclass(frozen=True, slots=True)
class FileProcessingReport:
    source: Path
    destination: Path
    success: bool
    message: str
    duration_ms: int
    matches_found: int = 0
    matches_applied: int = 0
    matches_skipped: int = 0
    detector_counts: dict[str, int] = field(default_factory=dict)
    detector_timings_ms: dict[str, int] = field(default_factory=dict)
    audit_trail: AuditTrail = field(default_factory=AuditTrail)


@dataclass(frozen=True, slots=True)
class AggregateStatistics:
    total_matches_found: int
    total_matches_applied: int
    total_matches_skipped: int
    detector_totals: dict[str, int]
    timeout_count: int = 0


@dataclass(frozen=True, slots=True)
class BatchProcessingReport:
    total: int
    success: int
    failed: int
    duration_ms: int
    files: list[FileProcessingReport]
    statistics: AggregateStatistics
