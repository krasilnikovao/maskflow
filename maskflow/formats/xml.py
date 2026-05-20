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
            ),
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

            # element.tail intentionally skipped — it is pretty-print whitespace,
            # not a field value.
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

    def _process_text_field(self, field_name: str, value: str) -> str | None:
        if self.field_engine is not None:
            return self.field_engine.process_field(field_name=field_name, value=value)
        return self.engine.process_text(value)

    def _write_masked_xml(
        self,
        source: Path,
        destination: Path,
        encoding: str,
    ) -> None:
        tree = etree.parse(str(source), parser=_safe_parser())
        root = tree.getroot()

        for element in root.iter():
            element_name = _local_name(element.tag) if isinstance(element.tag, str) else ""

            if element.text:
                processed = self._process_text_field(element_name, element.text)
                element.text = processed if processed is not None else ""

            for key in list(element.attrib.keys()):
                attribute_name = _local_name(key)
                value = element.attrib[key]
                processed_value = self._process_text_field(attribute_name, value)

                if processed_value is None:
                    del element.attrib[key]
                else:
                    element.attrib[key] = processed_value

        tree.write(
            str(destination),
            encoding=encoding,
            xml_declaration=True,
        )
