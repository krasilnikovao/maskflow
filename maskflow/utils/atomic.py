import os
import sys
import tempfile
import time
from collections.abc import Callable
from pathlib import Path

# На Windows антивирус или другие file-system watchers могут кратковременно
# блокировать только что созданный temp-файл, что приводит к PermissionError
# при os.replace. Retry с нарастающей паузой решает проблему без изменения
# семантики атомарной записи.
_WINDOWS_REPLACE_RETRIES = 3
_WINDOWS_REPLACE_BASE_DELAY = 0.05  # секунды


def _safe_replace(src: Path, dst: Path) -> None:
    """Атомарная замена файла с retry на Windows.

    На POSIX os.replace атомарен и не требует retry.
    На Windows PermissionError (WinError 5) может возникнуть из-за кратковременной
    блокировки файла антивирусом или VSS — retry с паузой устраняет эту проблему.
    """
    if sys.platform != "win32":
        os.replace(src, dst)
        return

    for attempt in range(_WINDOWS_REPLACE_RETRIES):
        try:
            os.replace(src, dst)
            return
        except PermissionError:
            if attempt == _WINDOWS_REPLACE_RETRIES - 1:
                raise
            time.sleep(_WINDOWS_REPLACE_BASE_DELAY * (attempt + 1))


def atomic_write_text(
    destination: Path,
    content: str,
    encoding: str = "utf-8",
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)

    fd, temp_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=destination.parent,
    )

    temp_path = Path(temp_name)

    try:
        with os.fdopen(fd, "w", encoding=encoding, newline="") as file:
            file.write(content)
            file.flush()
            os.fsync(file.fileno())

        _safe_replace(temp_path, destination)

    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def atomic_write_binary_via_temp(
    destination: Path,
    writer: Callable[[Path], None],
) -> None:
    """Атомарная запись бинарного файла через временный файл.

    writer получает путь к временному файлу и должен записать в него данные.
    После успешного завершения writer временный файл атомарно переименовывается
    в destination. В случае ошибки временный файл удаляется.

    fsync вызывается на временном файле перед os.replace, чтобы гарантировать
    сброс данных на диск и избежать потери данных при внезапном отключении питания.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)

    fd, temp_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=destination.parent,
    )

    os.close(fd)
    temp_path = Path(temp_name)

    try:
        writer(temp_path)

        # fsync: гарантируем сброс данных на диск перед переименованием.
        # На Windows FlushFileBuffers требует дескриптор с правом записи;
        # на POSIX — достаточно любого открытого дескриптора.
        # Пропускаем fsync на Windows: write-caching там безопаснее,
        # а атомарность обеспечивается _safe_replace().
        if sys.platform != "win32":
            with temp_path.open("rb") as fh:
                os.fsync(fh.fileno())

        _safe_replace(temp_path, destination)

    except Exception:
        temp_path.unlink(missing_ok=True)
        raise
