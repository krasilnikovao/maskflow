import os
import tempfile
from collections.abc import Callable
from pathlib import Path


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

        os.replace(temp_path, destination)

    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def atomic_write_binary_via_temp(
    destination: Path,
    writer: Callable[[Path], None],
) -> None:
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
        os.replace(temp_path, destination)

    except Exception:
        temp_path.unlink(missing_ok=True)
        raise
