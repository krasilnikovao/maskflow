from pathlib import Path

import typer

from maskflow.audit.json_export import export_audit_trail_json
from maskflow.audit.models import AuditTrail
from maskflow.cli.help import LocalizedTyperCommand
from maskflow.cli.i18n import tr
from maskflow.core.batch import BatchPipeline
from maskflow.core.directory import build_directory_tasks
from maskflow.reports.json_report import export_batch_report_json
from maskflow.rules.loader import RulesLoader
from maskflow.runtime.settings import get_settings
from maskflow.utils.logging import configure_logging, get_logger

logger = get_logger("maskflow.cli")


def register_batch_commands(app: typer.Typer) -> None:
    @app.command(
        "mask-dir",
        cls=LocalizedTyperCommand,
        help=tr("mask_dir_help"),
        epilog=tr("mask_dir_examples"),
    )
    def mask_dir(
        source_dir: Path = typer.Argument(..., metavar="SOURCE_DIR", help=tr("source_dir")),
        destination_dir: Path = typer.Argument(
            ..., metavar="DESTINATION_DIR", help=tr("destination_dir")
        ),
        config: Path = typer.Option(
            get_settings().default_config,
            "--config",
            "-c",
            help=tr("config"),
        ),
        workers: int | None = typer.Option(None, "--workers", "-w", help=tr("workers")),
        log_level: str = typer.Option(
            get_settings().log_level,
            "--log-level",
            help=tr("log_level"),
        ),
        json_logs: bool = typer.Option(False, "--json-logs", help=tr("json_logs")),
        overwrite: bool = typer.Option(False, "--overwrite", help=tr("overwrite")),
        report_path: Path | None = typer.Option(None, "--report", help=tr("report")),
        plugins_dir: Path | None = typer.Option(None, "--plugins-dir", help=tr("plugins_dir")),
        audit_report: Path | None = typer.Option(None, "--audit-report", help=tr("audit_report")),
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
