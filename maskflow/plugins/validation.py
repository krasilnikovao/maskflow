from maskflow.plugins.spec import PluginSpec

ALLOWED_PLUGIN_CAPABILITIES = {
    "detector",
    "masker",
    "field_rules",
}


def validate_plugin_spec(plugin: PluginSpec) -> None:
    if not plugin.name:
        raise ValueError("Plugin name must not be empty")

    if plugin.detector.name != plugin.name:
        raise ValueError(
            f"Plugin name mismatch: plugin={plugin.name}, detector={plugin.detector.name}"
        )

    if plugin.metadata is None:
        return

    if not plugin.metadata.name:
        raise ValueError("Plugin metadata name must not be empty")

    if not plugin.metadata.version:
        raise ValueError("Plugin metadata version must not be empty")

    invalid_capabilities = set(plugin.metadata.capabilities) - ALLOWED_PLUGIN_CAPABILITIES

    if invalid_capabilities:
        raise ValueError(f"Unsupported plugin capabilities: {sorted(invalid_capabilities)}")
