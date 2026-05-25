from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import ClassVar

from maskflow.core.types import Match


class BaseDetector(ABC):
    """Abstract base for all detectors.

    Concrete subclasses MUST declare a class-level ``name`` attribute.
    Intermediate abstract bases (e.g. RegexDetector) must set
    ``_abstract_base = True`` to opt out of the enforcement.
    """

    name: ClassVar[str]

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        # Intermediate abstract bases carry _abstract_base = True
        if cls.__dict__.get("_abstract_base"):
            return
        if not isinstance(cls.__dict__.get("name"), str):
            raise TypeError(
                f"{cls.__name__} must define a class-level `name: str` attribute"
            )

    @abstractmethod
    def detect(self, text: str) -> Iterable[Match]:
        raise NotImplementedError


class BaseMasker(ABC):
    """Abstract base for all maskers.

    Concrete subclasses MUST declare a class-level ``name`` attribute.
    Intermediate abstract bases must set ``_abstract_base = True`` to opt out
    of the enforcement.
    """

    name: ClassVar[str]

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls.__dict__.get("_abstract_base"):
            return
        if not isinstance(cls.__dict__.get("name"), str):
            raise TypeError(
                f"{cls.__name__} must define a class-level `name: str` attribute"
            )

    @abstractmethod
    def mask(self, value: str) -> str:
        raise NotImplementedError
