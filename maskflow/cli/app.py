from pathlib import Path

import typer

from maskflow.audit.json_export import export_audit_trail_json
from maskflow.audit.models import AuditTrail
from maskflow.core.batch import BatchPipeline
from maskflow.core.directory import build_directory_tasks
from maskflow.core.factory import build_engine_bundle_from_config
from maskflow.reports.json_report import export_batch_report_json
from maskflow.rules.loader import RulesLoader
from maskflow.services.file_masking import FileMaskingService
from maskflow.utils.encoding import detect_text_encoding
from maskflow.utils.logging import configure_logging, get_logger

logger = get_logger("maskflow.cli")

app = typer.Typer(
    help="MaskFlow enterprise data masking service",
    no_args_is_help=True,
)


@app.command()
def mask(
    source: Path = typer.Argument(..., help="Source file"),
    destination: Path = typer.Argument(..., help="Destination file"),
    config: Path = typer.Option(
        Path("configs/default.yaml"),
        "--config",
        "-c",
        help="Path to YAML config",
    ),
    log_level: str = typer.Option(
        "INFO",
        "--log-level",
        help="Logging level",
    ),
    json_logs: bool = typer.Option(
        False,
        "--json-logs",
        help="Enable JSON logs",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Analyze file without writing output",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite destination file if it already exists",
    ),
    plugins_dir: Path | None = typer.Option(
        None,
        "--plugins-dir",
        help="Directory with external plugins",
    ),
    audit_report: Path | None = typer.Option(
        None,
        "--audit-report",
        help="Write JSON audit trail report",
    ),
) -> None:
    configure_logging(
        level=log_level,
        json_logs=json_logs,
    )

    logger.info(
        "masking_started",
        source_suffix=source.suffix.lower(),
        config_path=str(config),
    )

    loaded_config = RulesLoader.load(config)

    bundle = build_engine_bundle_from_config(
        loaded_config,
        plugins_dir=plugins_dir,
    )

    engine = bundle.engine

    suffix = source.suffix.lower()

    if dry_run:
        if suffix == ".txt":
            text_encoding = detect_text_encoding(source)
            text = source.read_text(encoding=text_encoding, errors="replace")
            analysis = engine.analyze_text(text)

            typer.echo(f"Dry run completed. Matches found: {analysis.matches_applied}")

            logger.info(
                "dry_run_completed",
                source_suffix=suffix,
                matches_found=analysis.matches_found,
                matches_applied=analysis.matches_applied,
                matches_skipped=analysis.matches_skipped,
                detector_counts=analysis.detector_counts,
            )
            return

        raise typer.BadParameter(f"Dry run is not supported for format: {suffix}")

    service = FileMaskingService()

    try:
        file_report = service.process_file(
            source=source,
            destination=destination,
            config_path=config,
            overwrite=overwrite,
            plugins_dir=plugins_dir,
        )

        if audit_report is not None:
            export_audit_trail_json(
                audit_trail=file_report.audit_trail,
                destination=audit_report,
            )

            logger.info(
                "audit_report_written",
                audit_report=str(audit_report),
            )

    except ValueError as error:
        raise typer.BadParameter(str(error)) from error

    logger.info(
        "masking_finished",
        destination_suffix=destination.suffix.lower(),
    )

    typer.echo(f"Masked file written to: {destination}")


@app.command("mask-dir")
def mask_dir(
    source_dir: Path = typer.Argument(..., help="Source directory"),
    destination_dir: Path = typer.Argument(..., help="Destination directory"),
    config: Path = typer.Option(
        Path("configs/default.yaml"),
        "--config",
        "-c",
        help="Path to YAML config",
    ),
    workers: int | None = typer.Option(
        None,
        "--workers",
        "-w",
        help="Number of parallel workers. Overrides config runtime_limits.max_workers",
    ),
    log_level: str = typer.Option(
        "INFO",
        "--log-level",
        help="Logging level",
    ),
    json_logs: bool = typer.Option(
        False,
        "--json-logs",
        help="Enable JSON logs",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite destination files if they already exist",
    ),
    report_path: Path | None = typer.Option(
        None,
        "--report",
        help="Write JSON processing report",
    ),
    plugins_dir: Path | None = typer.Option(
        None,
        "--plugins-dir",
        help="Directory with external plugins",
    ),
    audit_report: Path | None = typer.Option(
        None,
        "--audit-report",
        help="Write JSON audit trail report",
    ),
) -> None:
    configure_logging(
        level=log_level,
        json_logs=json_logs,
    )

    loaded_config = RulesLoader.load(config)
    runtime_limits = loaded_config.runtime_limits

    logger.info(
        "mask_dir_started",
        source_dir=str(source_dir),
        destination_dir=str(destination_dir),
        workers=workers,
    )

    tasks = build_directory_tasks(
        source_dir=source_dir,
        destination_dir=destination_dir,
        config_path=config,
        overwrite=overwrite,
        timeout_seconds=runtime_limits.file_timeout_seconds,
        plugins_dir=plugins_dir,
    )

    destination_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    effective_workers = workers if workers is not None else runtime_limits.max_workers

    pipeline = BatchPipeline(max_workers=effective_workers)
    report = pipeline.process(tasks)

    if audit_report is not None:
        audit_trail = AuditTrail()

        for file_report in report.files:
            for event in file_report.audit_trail.events:
                audit_trail = audit_trail.add(event)

        export_audit_trail_json(
            audit_trail=audit_trail,
            destination=audit_report,
        )

        logger.info(
            "audit_report_written",
            audit_report=str(audit_report),
        )

    if report_path is not None:
        export_batch_report_json(
            report=report,
            destination=report_path,
        )

        logger.info(
            "batch_report_written",
            report_path=str(report_path),
        )

    success_count = report.success
    failed_count = report.failed

    logger.info(
        "mask_dir_finished",
        total=report.total,
        success=success_count,
        failed=failed_count,
        workers=effective_workers,
    )

    typer.echo(
        f"Directory masking completed. Total: {report.total}, "
        f"success: {success_count}, failed: {failed_count}"
    )

    if failed_count > 0:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
