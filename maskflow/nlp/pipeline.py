from collections.abc import Iterable

from maskflow.nlp.models import EntityCandidate, ResolvedEntity
from maskflow.nlp.providers.base import NlpProvider
from maskflow.nlp.resolver import NlpResolver


class NlpPipeline:
    def __init__(
        self,
        providers: list[NlpProvider],
        resolver: NlpResolver | None = None,
    ) -> None:
        self.providers = providers
        self.resolver = resolver or NlpResolver()

    def collect_candidates(self, text: str) -> list[EntityCandidate]:
        candidates: list[EntityCandidate] = []
        for provider in self.providers:
            candidates.extend(provider.detect(text))
        return candidates

    def detect(self, text: str) -> Iterable[ResolvedEntity]:
        return self.resolver.resolve(self.collect_candidates(text))
