import multiprocessing
import pickle
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError


class OperationTimeoutError(RuntimeError):
    pass


def _process_worker(
    operation: Callable[[], object],
    pipe: "multiprocessing.connection.Connection",
) -> None:
    try:
        result = operation()
        pipe.send(("ok", pickle.dumps(result)))
    except BaseException as error:  # noqa: BLE001 - перенаправляем в родительский процесс
        try:
            pipe.send(("err", pickle.dumps(error)))
        except Exception:
            pipe.send(("err", pickle.dumps(RuntimeError(repr(error)))))
    finally:
        pipe.close()


def run_with_timeout[T](
    operation: Callable[[], T],
    timeout_seconds: int | None,
    use_process: bool = False,
) -> T:
    """Запускает operation с жёстким таймаутом.

    use_process=True реально прерывает зависшую CPU-операцию (через terminate
    дочернего процесса). При False используется тред с попыткой cancel — может
    не прервать уже работающий синхронный код.
    """
    if timeout_seconds is None:
        return operation()

    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be greater than zero")

    if use_process:
        parent_pipe, child_pipe = multiprocessing.Pipe(duplex=False)
        process = multiprocessing.Process(
            target=_process_worker,
            args=(operation, child_pipe),
        )
        process.start()
        child_pipe.close()

        try:
            if not parent_pipe.poll(timeout_seconds):
                process.terminate()
                process.join(1)
                if process.is_alive():
                    process.kill()
                    process.join()
                raise OperationTimeoutError(
                    f"Operation timed out after {timeout_seconds} seconds"
                )

            status, payload = parent_pipe.recv()
        finally:
            parent_pipe.close()
            process.join()

        if status == "ok":
            return pickle.loads(payload)  # type: ignore[no-any-return]

        raise pickle.loads(payload)

    executor = ThreadPoolExecutor(max_workers=1)
    try:
        future = executor.submit(operation)
        try:
            return future.result(timeout=timeout_seconds)
        except FutureTimeoutError as error:
            raise OperationTimeoutError(
                f"Operation timed out after {timeout_seconds} seconds"
            ) from error
    finally:
        # не блокируемся ожиданием — лучше отпустить зависший тред.
        executor.shutdown(wait=False, cancel_futures=True)
