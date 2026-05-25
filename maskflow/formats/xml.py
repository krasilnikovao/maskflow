from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree  # type: ignore[import-untyped]

from maskflow.core.engine import MaskingEngine
from maskflow.core.types import AnalysisResult
from maskflow.rules.field_engine import FieldRuleEngine
from maskflow.utils.atomic import atomic_write_binary_via_temp


def _safe_parser() -> "etree.XMLParser":
    # resolve_entities=False blocks XXE / billion laughs
    return etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        huge_tree=False,
        load_dtd=False,
    )


def _local_name(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


@dataclass(slots=True)
class _XmlStats:
    matches_found: int = 0
    matches_applied: int = 0
    matches_skipped: int = 0
    detector_counts: Counter[str] = field(default_factory=Counter)
    detector_timings_ms: Counter[str] = field(default_factory=Counter)


class XmlProcessor:
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
        atomic_write_binary_via_temp(
            destination=destination,
            writer=lambda temp_path: self._write_masked_xml(
                source=source,
                destination=temp_path,
                encoding=encoding,
                stats=None,
            ),
        )

    def process_with_stats(
        self,
        source: Path,
        destination: Path,
        encoding: str = "utf-8",
    ) -> AnalysisResult:
        """FIX 1.2: единый проход — маскируем и собираем статистику."""
        stats = _XmlStats()

        atomic_write_binary_via_temp(
            destination=destination,
            writer=lambda temp_path: self._write_masked_xml(
                source=source,
                destination=temp_path,
                encoding=encoding,
                stats=stats,
            ),
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
    ) -> AnalysisResult:
        tree = etree.parse(str(source), parser=_safe_parser())
        root = tree.getroot()

        total_matches_found = 0
        total_matches_applied = 0
        total_matches_skipped = 0
        detector_counts: dict[str, int] = {}
        detector_timings_ms: dict[str, int] = {}

        for element in root.iter():
            values: list[str] = []

            if element.text:
                values.append(element.text)

            # FIX 2.4: обрабатываем tail если он содержит не-пробельный текст
            if element.tail and element.tail.strip():
                values.append(element.tail)

            values.extend(element.attrib.values())

            for value in values:
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

    def _mask_field(
        self,
        field_name: str,
        value: str,
        stats: _XmlStats | None,
    ) -> str | None:
        """Маскирует значение с учётом field_engine и накоплением статистики."""
        if self.field_engine is not None:
            rule = self.field_engine.rules.get(field_name.lower())
            if rule is not None:
                if rule.action == "remove":
                    return None
                if rule.action == "replace":
                    return rule.replacement or ""
                # action == "mask" — продолжаем

        if stats is not None:
            masked, analysis = self.engine.process_with_stats(value)
            stats.matches_found += analysis.matches_found
            stats.matches_applied += analysis.matches_applied
            stats.matches_skipped += analysis.matches_skipped
            stats.detector_counts.update(analysis.detector_counts)
            stats.detector_timings_ms.update(analysis.detector_timings_ms)
            return masked

        return self.engine.process_text(value)

    def _write_masked_xml(
        self,
        source: Path,
        destination: Path,
        encoding: str,
        stats: _XmlStats | None,
    ) -> None:
        tree = etree.parse(str(source), parser=_safe_parser())
        root = tree.getroot()

        for element in root.iter():
            element_name = _local_name(element.tag) if isinstance(element.tag, str) else ""

            if element.text:
                processed = self._mask_field(element_name, element.text, stats)
                element.text = processed if processed is not None else ""

            # FIX 2.4: маскируем tail если он содержит реальный текст
            if element.tail and element.tail.strip():
                parent = element.getparent()
                parent_name = (
                    _local_name(parent.tag)
                    if parent is not None and isinstance(parent.tag, str)
                    else ""
                )
                processed_tail = self._mask_field(parent_name, element.tail, stats)
                if processed_tail is not None:
                    element.tail = processed_tail
                # Если processed_tail is None (remove) — оставляем tail как есть,
                # т.к. удаление tail разрушит XML-структуру.

            for key in list(element.attrib.keys()):
                attribute_name = _local_name(key)
                value = element.attrib[key]
                processed_value = self._mask_field(attribute_name, value, stats)

                if processed_value is None:
                    del element.attrib[key]
                else:
                    element.attrib[key] = processed_value

        tree.write(
            str(destination),
            encoding=encoding,
            xml_declaration=True,
        )
