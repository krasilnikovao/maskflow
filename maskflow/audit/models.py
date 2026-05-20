from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AuditEvent:
    event_type: str
    source: Path | None = None
    destination: Path | None = None
    detector: str | None = None
    matches_found: int = 0
    matches_applied: int = 0
    matches_skipped: int = 0
    duration_ms: int = 0
    metadata: dict[str, str | int | bool] = field(default_factory=dict)


@dataclass(slots=True)
class AuditTrail:
    """Мутабельный журнал событий.

    Раньше add() копировал весь список — O(n²) на батче.
    Теперь обычный append — O(1).
    """

    events: list[AuditEvent] = field(default_factory=list)

    def add(self, event: AuditEvent) -> "AuditTrail":
        self.events.append(event)
        return self
