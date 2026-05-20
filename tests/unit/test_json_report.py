import json
from pathlib import Path

from maskflow.reports.json_report import export_batch_report_json
from maskflow.reports.models import (
    AggregateStatistics,
    BatchProcessingReport,
    FileProcessingReport,
)


def test_export_batch_report_json_writes_report(tmp_path: Path) -> None:
    destination = tmp_path / "audit" / "report.json"

    report = BatchProcessingReport(
        total=1,
        success=1,
        failed=0,
        duration_ms=123,
        files=[
            FileProcessingReport(
                source=tmp_path / "source.txt",
                destination=tmp_path / "masked.txt",
                success=True,
                message="OK",
                duration_ms=10,
                matches_found=1,
                matches_applied=1,
                matches_skipped=0,
                detector_counts={
                    "email": 1,
                },
            ),
        ],
        statistics=AggregateStatistics(
            total_matches_found=1,
            total_matches_applied=1,
            total_matches_skipped=0,
            detector_totals={"email": 1},
        ),
    )

    export_batch_report_json(
        report=report,
        destination=destination,
    )

    payload = json.loads(destination.read_text(encoding="utf-8"))

    assert payload["total"] == 1
    assert payload["success"] == 1
    assert payload["failed"] == 0
    assert payload["duration_ms"] == 123

    assert payload["files"][0]["success"] is True
    assert payload["files"][0]["message"] == "OK"
    assert payload["files"][0]["matches_found"] == 1
    assert payload["files"][0]["matches_applied"] == 1
    assert payload["files"][0]["detector_counts"] == {"email": 1}

    assert isinstance(payload["files"][0]["source"], str)
    assert isinstance(payload["files"][0]["destination"], str)


def test_export_batch_report_json_preserves_unicode(tmp_path: Path) -> None:
    destination = tmp_path / "report.json"

    report = BatchProcessingReport(
        total=1,
        success=1,
        failed=0,
        duration_ms=1,
        files=[
            FileProcessingReport(
                source=tmp_path / "исходный.txt",
                destination=tmp_path / "результат.txt",
                success=True,
                message="OK",
                duration_ms=1,
                matches_found=1,
                matches_applied=1,
                matches_skipped=0,
                detector_counts={"email": 1},
            ),
        ],
        statistics=AggregateStatistics(
            total_matches_found=1,
            total_matches_applied=1,
            total_matches_skipped=0,
            detector_totals={"email": 1},
        ),
    )

    export_batch_report_json(
        report=report,
        destination=destination,
    )

    content = destination.read_text(encoding="utf-8")

    assert "исходный.txt" in content
    assert "результат.txt" in content
