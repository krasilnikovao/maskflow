from pathlib import Path

import pytest
from cryptography.fernet import Fernet

from maskflow.storage.encrypted_mapping import EncryptedMappingStore


def test_encrypted_mapping_store_roundtrip(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    key = Fernet.generate_key().decode("utf-8")

    monkeypatch.setenv(
        "MASKFLOW_TEST_KEY",
        key,
    )

    path = tmp_path / "mapping.bin"

    store = EncryptedMappingStore(
        path=path,
        encryption_key_env="MASKFLOW_TEST_KEY",
    )

    store.set("masked", "original")
    store.save()

    loaded = EncryptedMappingStore(
        path=path,
        encryption_key_env="MASKFLOW_TEST_KEY",
    )

    assert loaded.get("masked") == "original"


def test_encrypted_mapping_store_requires_env_key(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="Environment variable is not set"):
        EncryptedMappingStore(
            path=tmp_path / "mapping.bin",
            encryption_key_env="MISSING_KEY",
        )


def test_encrypted_mapping_store_rejects_invalid_key(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "MASKFLOW_TEST_KEY",
        Fernet.generate_key().decode("utf-8"),
    )

    path = tmp_path / "mapping.bin"

    store = EncryptedMappingStore(
        path=path,
        encryption_key_env="MASKFLOW_TEST_KEY",
    )

    store.set("masked", "original")
    store.save()

    monkeypatch.setenv(
        "MASKFLOW_TEST_KEY",
        Fernet.generate_key().decode("utf-8"),
    )

    with pytest.raises(
        ValueError,
        match="Failed to decrypt reversible mapping store",
    ):
        EncryptedMappingStore(
            path=path,
            encryption_key_env="MASKFLOW_TEST_KEY",
        )
