# MaskFlow External Plugins

This directory is reserved for organization-specific plugins.

External plugins must not:

- send data to external services;
- log original sensitive values;
- store original values;
- perform network requests by default;
- mutate global runtime state.

Each plugin must expose:

```python
from maskflow.plugins.registry import PluginRegistry
from maskflow.plugins.spec import PluginSpec

def register_plugins(registry: PluginRegistry) -> None:
    registry.register(
        PluginSpec(
            name="custom_rule",
            detector=CustomDetector(),
            masker_factory=CustomMasker,
        )
    )
```
