import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from maskflow.core.engine import MaskingEngine
from maskflow.core.types import AnalysisResult
from maskflow.rules.field_engine import FieldRuleEngine
from maskflow.utils.atomic import atomic_write_text

JsonValue = dict[str, Any] | list[Any] | str | int | float | bool | None

_MAX_JSON_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB — предупреждение


class _Removed:
    """Sentinel: указывает, что ключ нужно удалить из родительского контейнера."""

    _instance: "_Removed | None" = None

    def __new__(cls) -> "_Removed":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance


REMOVE_FIELD = _Removed()


@dataclass(slots=True)
class _JsonStats:
    matches_found: int = 0
    matches_applied: int = 0
    matches_skipped: int = 0
    detector_counts: Counter[str] = field(default_factory=Counter)
    detector_timings_ms: Counter[str] = field(default_factory=Counter)


class JsonProcessor:
    def __init__(
        self,
        engine: MaskingEngine,
        field_engine: FieldRuleEngine | None = None,
    ) -> None:
        self.engine = engine
        self.field_engine = field_engine

    def process(
        self,
        source: Path,
        destination: Path,
        encoding: str = "utf-8",
    ) -> None:
        data = self._load_json(source, encoding)
        masked = self._mask_value(data, stats=None)

        if isinstance(masked, _Removed):
            masked = None

        atomic_write_text(
            destination=destination,
            content=json.dumps(
                masked,
                ensure_ascii=False,
                indent=2,
            ),
            encoding=encoding,
        )

    def process_with_stats(
        self,
        source: Path,
        destination: Path,
        encoding: str = "utf-8",
    ) -> AnalysisResult:
        """FIX 1.2: единый проход — маскируем и собираем статистику."""
        data = self._load_json(source, encoding)
        stats = _JsonStats()
        masked = self._mask_value(data, stats=stats)

        if isinstance(masked, _Removed):
            masked = None

        atomic_write_text(
            destination=destination,
            content=json.dumps(
                masked,
                ensure_ascii=False,
                indent=2,
            ),
            encoding=encoding,
        )

        return AnalysisResult(
            matches_found=stats.matches_found,
            matches_applied=stats.matches_applied,
            matches_skipped=stats.matches_skipped,
            detector_counts=dict(stats.detector_counts),
            detector_timings_ms=dict(stats.detector_timings_ms),
        )

    def analyze(
        self,
        source: Path,
        encoding: str = "utf-8",
    ) -> AnalysisResult:
        data = self._load_json(source, encoding)

        total_matches_found = 0
        total_matches_applied = 0
        total_matches_skipped = 0
        detector_counts: dict[str, int] = {}
        detector_timings_ms: dict[str, int] = {}

        for value, field_name in self._iter_string_values(data):
            # Если для поля задано remove/replace — реальных матчей не будет.
            if self.field_engine is not None and field_name is not None:
                rule = self.field_engine.rules.get(field_name.lower())
                if rule is not None and rule.action in {"remove", "replace"}:
                    continue

            analysis = self.engine.analyze_text(value)

            total_matches_found += analysis.matches_found
            total_matches_applied += analysis.matches_applied
            total_matches_skipped += analysis.matches_skipped

            for detector, count in analysis.detector_counts.items():
                detector_counts[detector] = detector_counts.get(detector, 0) + count

            for detector, duration in analysis.detector_timings_ms.items():
                detector_timings_ms[detector] = detector_timings_ms.get(detector, 0) + duration

        return AnalysisResult(
            matches_found=total_matches_found,
            matches_applied=total_matches_applied,
            matches_skipped=total_matches_skipped,
            detector_counts=detector_counts,
            detector_timings_ms=detector_timings_ms,
        )

    def _load_json(
        self,
        source: Path,
        encoding: str,
    ) -> JsonValue:
        # FIX 4.1: предупреждение о большом файле
        try:
            size = source.stat().st_size
            if size > _MAX_JSON_SIZE_BYTES:
                from maskflow.utils.logging import get_logger

                get_logger("maskflow.json").warning(
                    "large_json_file_loaded_into_memory",
                    path=str(source),
                    size_mb=size // (1024 * 1024),
                )
        except OSError:
            pass

        with source.open(encoding=encoding) as file:
            data: Any = json.load(file)

        return cast(JsonValue, data)

    def _mask_string(
        self,
        value: str,
        field_name: str | None,
        stats: _JsonStats | None,
    ) -> "str | _Removed":
        """Маскирует строку, учитывая field_engine и накапливая статистику."""
        if self.field_engine is not None and field_name is not None:
            rule = self.field_engine.rules.get(field_name.lower())
            if rule is not None:
                if rule.action == "remove":
                    return REMOVE_FIELD
                if rule.action == "replace":
                    return rule.replacement or ""
                # action == "mask" — падаем ниже к обычному маскированию

        if stats is not None:
            masked, analysis = self.engine.process_with_stats(value)
            stats.matches_found += analysis.matches_found
            stats.matches_applied += analysis.matches_applied
            stats.matches_skipped += analysis.matches_skipped
            stats.detector_counts.update(analysis.detector_counts)
            stats.detector_timings_ms.update(analysis.detector_timings_ms)
            return masked

        return self.engine.process_text(value)

    def _mask_value(
        self,
        value: JsonValue,
        field_name: str | None = None,
        stats: _JsonStats | None = None,
    ) -> "JsonValue | _Removed":
        if isinstance(value, dict):
            result: dict[str, Any] = {}

            for key, child in value.items():
                masked_child = self._mask_value(child, field_name=key, stats=stats)

                if isinstance(masked_child, _Removed):
                    continue

                result[key] = masked_child

            return result

        if isinstance(value, list):
            items: list[Any] = []
            for child in value:
                masked_child = self._mask_value(child, field_name=field_name, stats=stats)
                if isinstance(masked_child, _Removed):
                    continue
                items.append(masked_child)
            return items

        if isinstance(value, str):
            return self._mask_string(value, field_name, stats)

        return value

    def _iter_string_values(
        self,
        value: JsonValue,
        field_name: str | None = None,
    ) -> list[tuple[str, str | None]]:
        result: list[tuple[str, str | None]] = []

        if isinstance(value, dict):
            for key, child in value.items():
                result.extend(self._iter_string_values(child, key))

        elif isinstance(value, list):
            for child in value:
                result.extend(self._iter_string_values(child, field_name))

        elif isinstance(value, str):
            result.append((value, field_name))

        return result
