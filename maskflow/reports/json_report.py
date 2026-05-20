import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from maskflow.reports.models import BatchProcessingReport
from maskflow.utils.atomic import atomic_write_text


def export_batch_report_json(
    report: BatchProcessingReport,
    destination: Path,
) -> None:
    payload = _to_json_safe_dict(report)

    atomic_write_text(
        destination=destination,
        content=json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def _to_json_safe_dict(report: BatchProcessingReport) -> dict[str, Any]:
    payload = asdict(report)

    for file_report in payload["files"]:
        file_report["source"] = str(file_report["source"])
        file_report["destination"] = str(file_report["destination"])

    return payload
