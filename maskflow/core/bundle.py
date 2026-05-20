from dataclasses import dataclass

from maskflow.core.engine import MaskingEngine
from maskflow.storage.encrypted_mapping import EncryptedMappingStore
from maskflow.storage.entity_cache import EntityCache


@dataclass(frozen=True, slots=True)
class EngineBundle:
    engine: MaskingEngine
    entity_cache: EntityCache | None = None
    reversible_mapping: EncryptedMappingStore | None = None

    def save(self) -> None:
        if self.entity_cache is not None:
            self.entity_cache.save()

        if self.reversible_mapping is not None:
            self.reversible_mapping.save()
