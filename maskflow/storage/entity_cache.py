import json
from pathlib import Path

from maskflow.utils.atomic import atomic_write_text
from maskflow.utils.filelock import FileLock


class EntityCache:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._values: dict[str, str] = {}

        if self.path.exists():
            self._load_into(self.path, self._values)

    def get(self, key: str) -> str | None:
        return self._values.get(key)

    def set(self, key: str, value: str) -> None:
        self._values[key] = value

    def save(self) -> None:
        """Атомарная запись с merge: при многопроцессной обработке
        не теряем ключи, добавленные другими процессами."""
        lock_path = self.path.with_suffix(self.path.suffix + ".lock")

        with FileLock(lock_path):
            if self.path.exists():
                disk: dict[str, str] = {}
                self._load_into(self.path, disk)
                merged: dict[str, str] = dict(disk)
                merged.update(self._values)
                self._values = merged

            atomic_write_text(
                destination=self.path,
                content=json.dumps(
                    self._values,
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

    def _load_into(self, path: Path, target: dict[str, str]) -> None:
        data = json.loads(path.read_text(encoding="utf-8"))

        if not isinstance(data, dict):
            raise ValueError("Entity cache must be a JSON object")

        for key, value in data.items():
            target[str(key)] = str(value)
