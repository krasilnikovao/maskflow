from pathlib import Path

from typer.testing import CliRunner

from maskflow.cli.app import app

runner = CliRunner()


def write_config(
    path: Path,
    cache_path: Path,
) -> None:
    path.write_text(
        f"""
pipeline:
  deterministic_secret: "secret"

rules:
  email:
    enabled: true
    mode: hmac
    prefix: EMAIL

cache:
  enabled: true
  path: "{cache_path.as_posix()}"
""",
        encoding="utf-8",
    )


def test_entity_cache_persists_between_runs(tmp_path: Path) -> None:
    cache_path = tmp_path / "entity-cache.json"

    config = tmp_path / "config.yaml"

    source1 = tmp_path / "source1.txt"
    source2 = tmp_path / "source2.txt"

    destination1 = tmp_path / "masked1.txt"
    destination2 = tmp_path / "masked2.txt"

    write_config(
        config,
        cache_path,
    )

    source1.write_text(
        "admin@example.com",
        encoding="utf-8",
    )

    source2.write_text(
        "admin@example.com",
        encoding="utf-8",
    )

    result1 = runner.invoke(
        app,
        [
            "mask",
            str(source1),
            str(destination1),
            "--config",
            str(config),
        ],
    )

    assert result1.exit_code == 0

    assert cache_path.exists()

    masked1 = destination1.read_text(encoding="utf-8").strip()

    result2 = runner.invoke(
        app,
        [
            "mask",
            str(source2),
            str(destination2),
            "--config",
            str(config),
        ],
    )

    assert result2.exit_code == 0

    masked2 = destination2.read_text(encoding="utf-8").strip()

    assert masked1 == masked2


def test_entity_cache_does_not_store_plaintext_values(tmp_path: Path) -> None:
    cache_path = tmp_path / "entity-cache.json"

    config = tmp_path / "config.yaml"

    source = tmp_path / "source.txt"
    destination = tmp_path / "masked.txt"

    write_config(
        config,
        cache_path,
    )

    source.write_text(
        "admin@example.com",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "mask",
            str(source),
            str(destination),
            "--config",
            str(config),
        ],
    )

    assert result.exit_code == 0

    cache_content = cache_path.read_text(encoding="utf-8")

    assert "admin@example.com" not in cache_content
    assert "EMAIL_" in cache_content
