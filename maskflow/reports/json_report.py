import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, cast

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

    return cast(dict[str, Any], _json_safe(payload))


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)

    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}

    if isinstance(value, list | tuple):
        return [_json_safe(item) for item in value]

    return value
