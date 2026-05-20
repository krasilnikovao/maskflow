from pathlib import Path
from xml.etree import ElementTree as ET

from maskflow.core.engine import MaskingEngine
from maskflow.detectors.email import EmailDetector
from maskflow.formats.xml import XmlProcessor
from maskflow.maskers.hmac_masker import HmacMasker


def build_engine() -> MaskingEngine:
    return MaskingEngine(
        detectors=[EmailDetector()],
        maskers={
            "email": HmacMasker(
                secret="secret",
                prefix="EMAIL",
            ),
        },
    )


def test_xml_processor_masks_text_node(tmp_path: Path) -> None:
    source = tmp_path / "source.xml"
    destination = tmp_path / "masked.xml"

    source.write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<root>
  <email>admin@example.com</email>
</root>
""",
        encoding="utf-8",
    )

    processor = XmlProcessor(build_engine())

    processor.process(
        source=source,
        destination=destination,
    )

    content = destination.read_text(encoding="utf-8")

    assert "admin@example.com" not in content
    assert "EMAIL_" in content

    ET.parse(destination)


def test_xml_processor_masks_attribute(tmp_path: Path) -> None:
    source = tmp_path / "source.xml"
    destination = tmp_path / "masked.xml"

    source.write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<root>
  <user email="admin@example.com" />
</root>
""",
        encoding="utf-8",
    )

    processor = XmlProcessor(build_engine())

    processor.process(
        source=source,
        destination=destination,
    )

    content = destination.read_text(encoding="utf-8")

    assert "admin@example.com" not in content
    assert "EMAIL_" in content

    root = ET.parse(destination).getroot()
    user = root.find("user")

    assert user is not None
    assert user.attrib["email"].startswith("EMAIL_")


def test_xml_processor_analyze_returns_statistics(tmp_path: Path) -> None:
    source = tmp_path / "source.xml"

    source.write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<root>
  <email>admin@example.com</email>
</root>
""",
        encoding="utf-8",
    )

    processor = XmlProcessor(build_engine())

    analysis = processor.analyze(source)

    assert analysis.matches_found == 1
    assert analysis.matches_applied == 1
    assert analysis.detector_counts == {"email": 1}


def test_xml_processor_handles_nested_nodes(tmp_path: Path) -> None:
    source = tmp_path / "source.xml"
    destination = tmp_path / "masked.xml"

    source.write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<root>
  <users>
    <user>
      <contact>admin@example.com</contact>
    </user>
  </users>
</root>
""",
        encoding="utf-8",
    )

    processor = XmlProcessor(build_engine())

    processor.process(
        source=source,
        destination=destination,
    )

    content = destination.read_text(encoding="utf-8")

    assert "admin@example.com" not in content
    assert "EMAIL_" in content
    assert "<users>" in content
    assert "<contact>" in content

    ET.parse(destination)


def test_xml_processor_preserves_unicode(tmp_path: Path) -> None:
    source = tmp_path / "source.xml"
    destination = tmp_path / "masked.xml"

    source.write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<root>
  <name>Иван</name>
  <email>admin@example.com</email>
</root>
""",
        encoding="utf-8",
    )

    processor = XmlProcessor(build_engine())

    processor.process(
        source=source,
        destination=destination,
    )

    content = destination.read_text(encoding="utf-8")

    assert "Иван" in content
    assert "admin@example.com" not in content
    assert "EMAIL_" in content
