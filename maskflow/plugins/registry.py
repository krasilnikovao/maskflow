from maskflow.plugins.spec import PluginSpec
from maskflow.plugins.validation import validate_plugin_spec


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: dict[str, PluginSpec] = {}

    def register(self, plugin: PluginSpec) -> None:
        validate_plugin_spec(plugin)

        if plugin.name in self._plugins:
            raise ValueError(f"Plugin already registered: {plugin.name}")

        self._plugins[plugin.name] = plugin

    def get(self, name: str) -> PluginSpec:
        plugin = self._plugins.get(name)

        if plugin is None:
            raise ValueError(f"Unknown plugin: {name}")

        return plugin

    def has(self, name: str) -> bool:
        return name in self._plugins

    def all(self) -> dict[str, PluginSpec]:
        return self._plugins.copy()
