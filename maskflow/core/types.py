from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Match:
    detector: str
    start: int
    end: int
    value: str

    @property
    def length(self) -> int:
        return self.end - self.start


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    matches_found: int
    matches_applied: int
    matches_skipped: int
    detector_counts: dict[str, int]
    detector_timings_ms: dict[str, int]
