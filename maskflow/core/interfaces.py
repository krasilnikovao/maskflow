from abc import ABC, abstractmethod
from collections.abc import Iterable

from maskflow.core.types import Match


class BaseDetector(ABC):
    name: str

    @abstractmethod
    def detect(self, text: str) -> Iterable[Match]:
        raise NotImplementedError


class BaseMasker(ABC):
    name: str

    @abstractmethod
    def mask(self, value: str) -> str:
        raise NotImplementedError
