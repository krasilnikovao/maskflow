from collections.abc import Iterable

import pytest

from maskflow.core.interfaces import BaseDetector
from maskflow.core.types import Match
from maskflow.maskers.hmac_masker import HmacMasker
from maskflow.plugins.registry import PluginRegistry
from maskflow.plugins.spec import PluginMetadata, PluginSpec


class DummyDetector(BaseDetector):
    name = "dummy"

    def detect(self, text: str) -> Iterable[Match]:
        return []


def test_plugin_registry_rejects_duplicate_plugin() -> None:
    registry = PluginRegistry()

    plugin = PluginSpec(
        name="dummy",
        detector=DummyDetector(),
        masker_factory=HmacMasker,
    )

    registry.register(plugin)

    with pytest.raises(ValueError, match="Plugin already registered: dummy"):
        registry.register(plugin)


def test_plugin_registry_rejects_detector_name_mismatch() -> None:
    registry = PluginRegistry()

    plugin = PluginSpec(
        name="other",
        detector=DummyDetector(),
        masker_factory=HmacMasker,
    )

    with pytest.raises(ValueError, match="Plugin name mismatch"):
        registry.register(plugin)


def test_plugin_registry_rejects_empty_plugin_name() -> None:
    registry = PluginRegistry()

    plugin = PluginSpec(
        name="",
        detector=DummyDetector(),
        masker_factory=HmacMasker,
    )

    with pytest.raises(ValueError, match="Plugin name must not be empty"):
        registry.register(plugin)


def test_plugin_registry_rejects_empty_metadata_name() -> None:
    registry = PluginRegistry()

    plugin = PluginSpec(
        name="dummy",
        detector=DummyDetector(),
        masker_factory=HmacMasker,
        metadata=PluginMetadata(
            name="",
            version="1.0.0",
        ),
    )

    with pytest.raises(ValueError, match="Plugin metadata name must not be empty"):
        registry.register(plugin)


def test_plugin_registry_rejects_empty_metadata_version() -> None:
    registry = PluginRegistry()

    plugin = PluginSpec(
        name="dummy",
        detector=DummyDetector(),
        masker_factory=HmacMasker,
        metadata=PluginMetadata(
            name="dummy",
            version="",
        ),
    )

    with pytest.raises(ValueError, match="Plugin metadata version must not be empty"):
        registry.register(plugin)


def test_plugin_registry_rejects_unsupported_capabilities() -> None:
    registry = PluginRegistry()

    plugin = PluginSpec(
        name="dummy",
        detector=DummyDetector(),
        masker_factory=HmacMasker,
        metadata=PluginMetadata(
            name="dummy",
            version="1.0.0",
            capabilities=("network",),
        ),
    )

    with pytest.raises(ValueError, match="Unsupported plugin capabilities"):
        registry.register(plugin)


def test_plugin_registry_accepts_valid_metadata() -> None:
    registry = PluginRegistry()

    plugin = PluginSpec(
        name="dummy",
        detector=DummyDetector(),
        masker_factory=HmacMasker,
        metadata=PluginMetadata(
            name="dummy",
            version="1.0.0",
            capabilities=("detector",),
        ),
    )

    registry.register(plugin)

    assert registry.has("dummy")
