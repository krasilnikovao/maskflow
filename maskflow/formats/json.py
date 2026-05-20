import json
from pathlib import Path
from typing import Any, cast

from maskflow.core.engine import MaskingEngine
from maskflow.core.types import AnalysisResult
from maskflow.rules.field_engine import FieldRuleEngine
from maskflow.utils.atomic import atomic_write_text

JsonValue = dict[str, Any] | list[Any] | str | int | float | bool | None


class _Removed:
    """Sentinel: указывает, что ключ нужно удалить из родительского контейнера."""

    _instance: "_Removed | None" = None

    def __new__(cls) -> "_Removed":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance


REMOVE_FIELD = _Removed()


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
        masked = self._mask_value(data)

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
        with source.open(encoding=encoding) as file:
            data: Any = json.load(file)

        return cast(JsonValue, data)

    def _mask_value(
        self,
        value: JsonValue,
        field_name: str | None = None,
    ) -> JsonValue | _Removed:
        if isinstance(value, dict):
            result: dict[str, Any] = {}

            for key, child in value.items():
                masked_child = self._mask_value(child, field_name=key)

                if isinstance(masked_child, _Removed):
                    continue

                result[key] = masked_child

            return result

        if isinstance(value, list):
            items: list[Any] = []
            for child in value:
                masked_child = self._mask_value(child, field_name=field_name)
                if isinstance(masked_child, _Removed):
                    # remove-правило применённое к элементу массива → отбрасываем
                    continue
                items.append(masked_child)
            return items

        if isinstance(value, str):
            if self.field_engine is not None and field_name is not None:
                processed = self.field_engine.process_field(
                    field_name=field_name,
                    value=value,
                )

                if processed is None:
                    return REMOVE_FIELD

                return processed

            return self.engine.process_text(value)

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
