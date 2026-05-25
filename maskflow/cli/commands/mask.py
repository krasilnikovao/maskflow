from pathlib import Path

import typer

from maskflow.audit.json_export import export_audit_trail_json
from maskflow.cli.help import LocalizedTyperCommand
from maskflow.cli.i18n import tr
from maskflow.core.factory import build_engine_bundle_from_config
from maskflow.rules.loader import RulesLoader
from maskflow.runtime.settings import get_settings
from maskflow.services.file_masking import FileMaskingService
from maskflow.utils.encoding import detect_text_encoding
from maskflow.utils.logging import configure_logging, get_logger

logger = get_logger("maskflow.cli")


def register_mask_commands(app: typer.Typer) -> None:
    @app.command(
        cls=LocalizedTyperCommand,
        help=tr("mask_help"),
        epilog=tr("mask_examples"),
    )
    def mask(
        source: Path = typer.Argument(..., metavar="SOURCE", help=tr("source_file")),
        destination: Path = typer.Argument(..., metavar="DESTINATION", help=tr("destination_file")),
        config: Path = typer.Option(
            get_settings().default_config,
            "--config",
            "-c",
            help=tr("config"),
        ),
        log_level: str = typer.Option(
            get_settings().log_level,
            "--log-level",
            help=tr("log_level"),
        ),
        json_logs: bool = typer.Option(False, "--json-logs", help=tr("json_logs")),
        dry_run: bool = typer.Option(False, "--dry-run", help=tr("dry_run")),
        overwrite: bool = typer.Option(False, "--overwrite", help=tr("overwrite")),
        plugins_dir: Path | None = typer.Option(None, "--plugins-dir", help=tr("plugins_dir")),
        audit_report: Path | None = typer.Option(None, "--audit-report", help=tr("audit_report")),
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
