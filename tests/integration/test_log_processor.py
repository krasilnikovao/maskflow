"""Тесты для LogProcessor: структурные элементы сохраняются, PII маскируется."""

from pathlib import Path

from maskflow.core.engine import MaskingEngine
from maskflow.detectors.email import EmailDetector
from maskflow.detectors.phone import PhoneDetector
from maskflow.formats.log import LogProcessor
from maskflow.maskers.hmac_masker import HmacMasker


def build_engine() -> MaskingEngine:
    return MaskingEngine(
        detectors=[EmailDetector(), PhoneDetector()],
        maskers={
            "email": HmacMasker(secret="secret", prefix="EMAIL"),
            "phone": HmacMasker(secret="secret", prefix="PHONE"),
        },
    )


# ---------------------------------------------------------------------------
# Защита stack traces
# ---------------------------------------------------------------------------


def test_log_processor_preserves_java_stack_trace(tmp_path: Path) -> None:
    source = tmp_path / "app.log"
    destination = tmp_path / "masked.log"

    trace_line = "    at com.example.Service.process(Service.java:42)\n"
    source.write_text(trace_line, encoding="utf-8")

    LogProcessor(build_engine()).process(source, destination)

    assert destination.read_text(encoding="utf-8") == trace_line


def test_log_processor_preserves_python_stack_trace(tmp_path: Path) -> None:
    source = tmp_path / "app.log"
    destination = tmp_path / "masked.log"

    trace_line = '  File "/app/service.py", line 42, in process\n'
    source.write_text(trace_line, encoding="utf-8")

    LogProcessor(build_engine()).process(source, destination)

    assert destination.read_text(encoding="utf-8") == trace_line


def test_log_processor_preserves_caused_by_line(tmp_path: Path) -> None:
    source = tmp_path / "app.log"
    destination = tmp_path / "masked.log"

    line = "Caused by: java.lang.NullPointerException\n"
    source.write_text(line, encoding="utf-8")

    LogProcessor(build_engine()).process(source, destination)

    assert destination.read_text(encoding="utf-8") == line


# ---------------------------------------------------------------------------
# Защита timestamp + level
# ---------------------------------------------------------------------------


def test_log_processor_preserves_iso_timestamp(tmp_path: Path) -> None:
    source = tmp_path / "app.log"
    destination = tmp_path / "masked.log"

    timestamp = "2024-01-15 10:23:45,123"
    line = f"{timestamp} INFO  root - user logged in: admin@example.com\n"
    source.write_text(line, encoding="utf-8")

    LogProcessor(build_engine()).process(source, destination)

    result = destination.read_text(encoding="utf-8")
    assert timestamp in result
    assert "INFO" in result
    assert "admin@example.com" not in result
    assert "EMAIL_" in result


def test_log_processor_preserves_iso_t_timestamp(tmp_path: Path) -> None:
    source = tmp_path / "app.log"
    destination = tmp_path / "masked.log"

    timestamp = "2024-01-15T10:23:45.123Z"
    line = f"{timestamp} [ERROR] contact: admin@example.com\n"
    source.write_text(line, encoding="utf-8")

    LogProcessor(build_engine()).process(source, destination)

    result = destination.read_text(encoding="utf-8")
    assert timestamp in result
    assert "[ERROR]" in result
    assert "admin@example.com" not in result


def test_log_processor_preserves_1c_techlog_prefix(tmp_path: Path) -> None:
    source = tmp_path / "app.log"
    destination = tmp_path / "masked.log"

    prefix = "{10:23:45.123-0,PROC,5}"
    line = f"{prefix}event=Connect,user=admin@example.com\n"
    source.write_text(line, encoding="utf-8")

    LogProcessor(build_engine()).process(source, destination)

    result = destination.read_text(encoding="utf-8")
    assert prefix in result
    assert "admin@example.com" not in result


# ---------------------------------------------------------------------------
# Маскировка PII в message
# ---------------------------------------------------------------------------


def test_log_processor_masks_email_in_message(tmp_path: Path) -> None:
    source = tmp_path / "app.log"
    destination = tmp_path / "masked.log"

    source.write_text(
        "2024-01-15 10:23:45,123 INFO app - sending email to user@company.ru\n",
        encoding="utf-8",
    )

    LogProcessor(build_engine()).process(source, destination)

    result = destination.read_text(encoding="utf-8")
    assert "user@company.ru" not in result
    assert "EMAIL_" in result


def test_log_processor_masks_phone_in_message(tmp_path: Path) -> None:
    source = tmp_path / "app.log"
    destination = tmp_path / "masked.log"

    source.write_text(
        "2024-01-15 10:23:45,123 INFO app - called +79991234567\n",
        encoding="utf-8",
    )

    LogProcessor(build_engine()).process(source, destination)

    result = destination.read_text(encoding="utf-8")
    assert "+79991234567" not in result
    assert "PHONE_" in result


def test_log_processor_multiline_mixed(tmp_path: Path) -> None:
    """Смешанный файл: лог + stack trace + PII."""
    source = tmp_path / "app.log"
    destination = tmp_path / "masked.log"

    content = (
        "2024-01-15 10:23:45,123 ERROR app - failed for user@example.com\n"
        "java.lang.RuntimeException: connection refused\n"
        "    at com.example.Client.connect(Client.java:99)\n"
        "    at com.example.Service.call(Service.java:42)\n"
        "2024-01-15 10:23:46,000 INFO  app - retry scheduled\n"
    )
    source.write_text(content, encoding="utf-8")

    LogProcessor(build_engine()).process(source, destination)

    result = destination.read_text(encoding="utf-8")

    # PII замаскирован
    assert "user@example.com" not in result
    # Stack trace сохранён
    assert "    at com.example.Client.connect(Client.java:99)\n" in result
    assert "    at com.example.Service.call(Service.java:42)\n" in result
    # Структура лога сохранена
    assert "2024-01-15 10:23:46,000" in result


# ---------------------------------------------------------------------------
# process_with_stats
# ---------------------------------------------------------------------------


def test_log_processor_process_with_stats(tmp_path: Path) -> None:
    source = tmp_path / "app.log"
    destination = tmp_path / "masked.log"

    source.write_text(
        "2024-01-15 10:23:45,123 INFO app - email: user@example.com\n"
        "    at com.example.Stack(Stack.java:1)\n",
        encoding="utf-8",
    )

    analysis = LogProcessor(build_engine()).process_with_stats(source, destination)

    assert analysis.matches_found == 1
    assert analysis.matches_applied == 1
    assert analysis.detector_counts == {"email": 1}
