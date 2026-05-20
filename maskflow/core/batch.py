import time
from collections import Counter
from collections.abc import Iterable
from concurrent.futures import ProcessPoolExecutor, as_completed

from maskflow.core.tasks import FileTask
from maskflow.reports.models import (
    AggregateStatistics,
    BatchProcessingReport,
    FileProcessingReport,
)
from maskflow.services.file_masking import FileMaskingService
from maskflow.utils.timeout import OperationTimeoutError, run_with_timeout


def process_file_task(task: FileTask) -> FileProcessingReport:
    service = FileMaskingService()

    started_at = time.perf_counter()

    try:
        return run_with_timeout(
            operation=lambda: service.process_file(
                source=task.source,
                destination=task.destination,
                config_path=task.config_path,
                overwrite=task.overwrite,
                plugins_dir=task.plugins_dir,
            ),
            timeout_seconds=task.timeout_seconds,
        )

    except OperationTimeoutError as error:
        return FileProcessingReport(
            source=task.source,
            destination=task.destination,
            success=False,
            message=f"OperationTimeoutError: {error}",
            duration_ms=int((time.perf_counter() - started_at) * 1000),
        )

    except Exception as error:
        return FileProcessingReport(
            source=task.source,
            destination=task.destination,
            success=False,
            message=f"{type(error).__name__}: {error}",
            duration_ms=int((time.perf_counter() - started_at) * 1000),
        )


class BatchPipeline:
    def __init__(
        self,
        max_workers: int = 1,
    ) -> None:
        if max_workers <= 0:
            raise ValueError("max_workers must be greater than zero")

        self.max_workers = max_workers

    def process(self, tasks: Iterable[FileTask]) -> BatchProcessingReport:
        started_at = time.perf_counter()

        task_list = list(tasks)

        if self.max_workers == 1:
            file_reports = [process_file_task(task) for task in task_list]
        else:
            file_reports = []

            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                futures = [
                    executor.submit(
                        process_file_task,
                        task,
                    )
                    for task in task_list
                ]

                for future in as_completed(futures):
                    file_reports.append(future.result())

        success_count = sum(1 for report in file_reports if report.success)
        failed_count = len(file_reports) - success_count

        detector_totals: Counter[str] = Counter()

        total_matches_found = 0
        total_matches_applied = 0
        total_matches_skipped = 0

        for report in file_reports:
            total_matches_found += report.matches_found
            total_matches_applied += report.matches_applied
            total_matches_skipped += report.matches_skipped
            detector_totals.update(report.detector_counts)

        timeout_count = sum(
            1 for report in file_reports if report.message.startswith("OperationTimeoutError")
        )

        return BatchProcessingReport(
            total=len(file_reports),
            success=success_count,
            failed=failed_count,
            duration_ms=int((time.perf_counter() - started_at) * 1000),
            files=file_reports,
            statistics=AggregateStatistics(
                total_matches_found=total_matches_found,
                total_matches_applied=total_matches_applied,
                total_matches_skipped=total_matches_skipped,
                detector_totals=dict(detector_totals),
                timeout_count=timeout_count,
            ),
        )
