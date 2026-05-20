from maskflow.detectors.email import EmailDetector
from maskflow.detectors.guid import GuidDetector
from maskflow.detectors.inn import InnDetector
from maskflow.detectors.phone import PhoneDetector
from maskflow.maskers.hmac_masker import HmacMasker
from maskflow.plugins.registry import PluginRegistry
from maskflow.plugins.spec import PluginSpec


def build_builtin_plugin_registry() -> PluginRegistry:
    registry = PluginRegistry()

    registry.register(
        PluginSpec(
            name="email",
            detector=EmailDetector(),
            masker_factory=HmacMasker,
        ),
    )

    registry.register(
        PluginSpec(
            name="phone",
            detector=PhoneDetector(),
            masker_factory=HmacMasker,
        ),
    )

    registry.register(
        PluginSpec(
            name="inn",
            detector=InnDetector(),
            masker_factory=HmacMasker,
        ),
    )

    registry.register(
        PluginSpec(
            name="guid",
            detector=GuidDetector(),
            masker_factory=HmacMasker,
        ),
    )

    return registry
