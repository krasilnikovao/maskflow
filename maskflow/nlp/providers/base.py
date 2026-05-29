from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import ClassVar

from maskflow.nlp.models import EntityCandidate


class NlpProvider(ABC):
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
    def detect(self, text: str) -> Iterable[EntityCandidate]:
        raise NotImplementedError
