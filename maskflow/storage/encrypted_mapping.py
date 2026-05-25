import json
import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from maskflow.utils.atomic import atomic_write_binary_via_temp
from maskflow.utils.filelock import FileLock


class EncryptedMappingStore:
    def __init__(
        self,
        path: Path,
        encryption_key_env: str,
    ) -> None:
        self.path = path
        self.encryption_key_env = encryption_key_env

        key = os.getenv(encryption_key_env)

        if not key:
            raise ValueError(
                f"Environment variable is not set: {encryption_key_env} "
                "(set a Fernet key, i.e. base64url-encoded 32 bytes)"
            )

        try:
            self._fernet = Fernet(key.encode("utf-8"))
        except Exception as error:
            raise ValueError(
                f"Invalid Fernet key in {encryption_key_env}: {type(error).__name__}"
            ) from error

        self._values: dict[str, str] = {}

        if self.path.exists():
            self._load_from(self.path)

    def get(self, key: str) -> str | None:
        return self._values.get(key)

    def set(self, key: str, value: str) -> None:
        self._values[key] = value

    def all(self) -> dict[str, str]:
        return self._values.copy()

    def save(self) -> None:
        """Atomic write + cross-process merge to avoid last-writer-wins."""
        lock_path = self.path.with_suffix(self.path.suffix + ".lock")

        with FileLock(lock_path):
            if self.path.exists():
                disk: dict[str, str] = {}
                self._load_into(self.path, disk)
                merged: dict[str, str] = dict(disk)
                merged.update(self._values)
                self._values = merged

            payload = json.dumps(
                self._values,
                ensure_ascii=False,
                indent=2,
            ).encode("utf-8")

            encrypted = self._fernet.encrypt(payload)

            def _write_encrypted(temp_path: Path) -> None:
                temp_path.write_bytes(encrypted)

            atomic_write_binary_via_temp(
                destination=self.path,
                writer=_write_encrypted,
            )

    def _load_from(self, path: Path) -> None:
        self._load_into(path, self._values)

    def _load_into(self, path: Path, target: dict[str, str]) -> None:
        encrypted = path.read_bytes()

        try:
            decrypted = self._fernet.decrypt(encrypted)
        except InvalidToken as error:
            raise ValueError("Failed to decrypt reversible mapping store") from error

        data = json.loads(decrypted.decode("utf-8"))

        if not isinstance(data, dict):
            raise ValueError("Reversible mapping store must contain JSON object")

        for key, value in data.items():
            target[str(key)] = str(value)
