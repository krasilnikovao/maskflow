from dataclasses import dataclass, field
from pathlib import Path

from maskflow.core.factory import build_engine_bundle_from_config
from maskflow.rules.loader import RulesLoader


@dataclass(frozen=True, slots=True)
class TextMaskingResult:
    masked_text: str
    matches_found: int
    matches_applied: int
    matches_skipped: int
    detector_counts: dict[str, int] = field(default_factory=dict)
    detector_timings_ms: dict[str, int] = field(default_factory=dict)


class TextMaskingService:
    def mask_text(
        self,
        text: str,
        config_path: Path,
        plugins_dir: Path | None = None,
    ) -> TextMaskingResult:
        config = RulesLoader.load(config_path)
        bundle = build_engine_bundle_from_config(
            config,
            plugins_dir=plugins_dir,
        )

        masked_text, analysis = bundle.engine.process_with_stats(text)
        bundle.save()

        return TextMaskingResult(
            masked_text=masked_text,
            matches_found=analysis.matches_found,
            matches_applied=analysis.matches_applied,
            matches_skipped=analysis.matches_skipped,
            detector_counts=analysis.detector_counts,
            detector_timings_ms=analysis.detector_timings_ms,
        )
