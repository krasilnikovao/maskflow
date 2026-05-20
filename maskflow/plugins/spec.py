from collections.abc import Callable
from dataclasses import dataclass

from maskflow.core.interfaces import BaseDetector, BaseMasker
from maskflow.storage.encrypted_mapping import EncryptedMappingStore
from maskflow.storage.entity_cache import EntityCache

MaskerFactory = Callable[
    [str, str, EntityCache | None, EncryptedMappingStore | None],
    BaseMasker,
]


@dataclass(frozen=True, slots=True)
class PluginMetadata:
    name: str
    version: str
    capabilities: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PluginSpec:
    name: str
    detector: BaseDetector
    masker_factory: MaskerFactory
    metadata: PluginMetadata | None = None
