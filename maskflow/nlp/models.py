from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EntityCandidate:
    entity_type: str
    start: int
    end: int
    value: str
    source: str
    confidence: float | None = None
    priority: int = 0

    @property
    def length(self) -> int:
        return self.end - self.start

    def __post_init__(self) -> None:
        if not self.entity_type:
            raise ValueError("entity_type must not be empty")
        if not self.source:
            raise ValueError("source must not be empty")
        if self.start < 0:
            raise ValueError("start must not be negative")
        if self.end <= self.start:
            raise ValueError("end must be greater than start")
        if self.confidence is not None and not (0.0 <= self.confidence <= 1.0):
            raise ValueError("confidence must be between 0.0 and 1.0")


@dataclass(frozen=True, slots=True)
class ResolvedEntity:
    entity_type: str
    start: int
    end: int
    value: str
    sources: tuple[str, ...]
    confidence: float | None = None

    @property
    def length(self) -> int:
        return self.end - self.start
