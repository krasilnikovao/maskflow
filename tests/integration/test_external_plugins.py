from pathlib import Path

from typer.testing import CliRunner

from maskflow.cli.app import app

runner = CliRunner()


def write_config(path: Path) -> None:
    path.write_text(
        """
pipeline:
  deterministic_secret: "secret"

rules:
  custom_code:
    enabled: true
    mode: hmac
    prefix: CUSTOM
""",
        encoding="utf-8",
    )


def test_cli_loads_external_plugin_for_single_file(tmp_path: Path) -> None:
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    plugin_file = plugins_dir / "custom_code_plugin.py"
    plugin_file.write_text(
        """
import regex

from maskflow.detectors.regex_base import RegexDetector
from maskflow.maskers.hmac_masker import HmacMasker
from maskflow.plugins.registry import PluginRegistry
from maskflow.plugins.spec import PluginSpec


CUSTOM_CODE_REGEX = regex.compile(r"CODE-[0-9]{4}")


class CustomCodeDetector(RegexDetector):
    name = "custom_code"
    pattern = CUSTOM_CODE_REGEX


def register_plugins(registry: PluginRegistry) -> None:
    registry.register(
        PluginSpec(
            name="custom_code",
            detector=CustomCodeDetector(),
            masker_factory=HmacMasker,
        ),
    )
""",
        encoding="utf-8",
    )

    config = tmp_path / "config.yaml"
    source = tmp_path / "source.txt"
    destination = tmp_path / "masked.txt"

    write_config(config)
    source.write_text("Internal code: CODE-1234", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "mask",
            str(source),
            str(destination),
            "--config",
            str(config),
            "--plugins-dir",
            str(plugins_dir),
        ],
    )

    assert result.exit_code == 0

    masked = destination.read_text(encoding="utf-8")

    assert "CODE-1234" not in masked
    assert "CUSTOM_" in masked


def test_cli_loads_external_plugin_for_mask_dir(tmp_path: Path) -> None:
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    plugin_file = plugins_dir / "custom_code_plugin.py"
    plugin_file.write_text(
        """
import regex

from maskflow.detectors.regex_base import RegexDetector
from maskflow.maskers.hmac_masker import HmacMasker
from maskflow.plugins.registry import PluginRegistry
from maskflow.plugins.spec import PluginSpec


CUSTOM_CODE_REGEX = regex.compile(r"CODE-[0-9]{4}")


class CustomCodeDetector(RegexDetector):
    name = "custom_code"
    pattern = CUSTOM_CODE_REGEX


def register_plugins(registry: PluginRegistry) -> None:
    registry.register(
        PluginSpec(
            name="custom_code",
            detector=CustomCodeDetector(),
            masker_factory=HmacMasker,
        ),
    )
""",
        encoding="utf-8",
    )

    config = tmp_path / "config.yaml"
    source_dir = tmp_path / "source"
    destination_dir = tmp_path / "destination"

    source_dir.mkdir()

    write_config(config)
    (source_dir / "source.txt").write_text(
        "Internal code: CODE-1234",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "mask-dir",
            str(source_dir),
            str(destination_dir),
            "--config",
            str(config),
            "--plugins-dir",
            str(plugins_dir),
        ],
    )

    assert result.exit_code == 0

    masked = (destination_dir / "source.txt").read_text(encoding="utf-8")

    assert "CODE-1234" not in masked
    assert "CUSTOM_" in masked
