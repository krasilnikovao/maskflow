import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from maskflow.audit.models import AuditTrail
from maskflow.utils.atomic import atomic_write_text


def export_audit_trail_json(
    audit_trail: AuditTrail,
    destination: Path,
) -> None:
    payload = _to_json_safe_dict(audit_trail)

    atomic_write_text(
        destination=destination,
        content=json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def _to_json_safe_dict(audit_trail: AuditTrail) -> dict[str, Any]:
    payload = asdict(audit_trail)

    for event in payload["events"]:
        if event["source"] is not None:
            event["source"] = str(event["source"])

        if event["destination"] is not None:
            event["destination"] = str(event["destination"])

    return payload
