from collections.abc import Iterable

from maskflow.nlp.models import EntityCandidate, ResolvedEntity


class NlpResolver:
    def __init__(self, min_confidence: float = 0.0) -> None:
        if not (0.0 <= min_confidence <= 1.0):
            raise ValueError("min_confidence must be between 0.0 and 1.0")

        self.min_confidence = min_confidence

    def resolve(self, candidates: Iterable[EntityCandidate]) -> list[ResolvedEntity]:
        filtered_candidates = [
            candidate
            for candidate in candidates
            if candidate.confidence is None or candidate.confidence >= self.min_confidence
        ]

        clusters = _cluster_overlapping(filtered_candidates)
        resolved = [_resolve_cluster(cluster) for cluster in clusters]

        return sorted(resolved, key=lambda entity: (entity.start, entity.end))


def _cluster_overlapping(
    candidates: list[EntityCandidate],
) -> list[list[EntityCandidate]]:
    sorted_candidates = sorted(
        candidates,
        key=lambda candidate: (candidate.start, candidate.end),
    )
    clusters: list[list[EntityCandidate]] = []
    current_cluster: list[EntityCandidate] = []
    current_end = -1

    for candidate in sorted_candidates:
        if not current_cluster:
            current_cluster = [candidate]
            current_end = candidate.end
            continue

        if candidate.start < current_end:
            current_cluster.append(candidate)
            current_end = max(current_end, candidate.end)
            continue

        clusters.append(current_cluster)
        current_cluster = [candidate]
        current_end = candidate.end

    if current_cluster:
        clusters.append(current_cluster)

    return clusters


def _resolve_cluster(cluster: list[EntityCandidate]) -> ResolvedEntity:
    by_type: dict[str, list[EntityCandidate]] = {}
    for candidate in cluster:
        by_type.setdefault(candidate.entity_type, []).append(candidate)

    type_winners = [
        _select_best_candidate(type_candidates)
        for type_candidates in by_type.values()
    ]
    winner = _select_best_candidate(type_winners)
    same_type_candidates = by_type[winner.entity_type]
    sources = tuple(sorted({candidate.source for candidate in same_type_candidates}))
    confidence = _max_confidence(same_type_candidates)

    return ResolvedEntity(
        entity_type=winner.entity_type,
        start=winner.start,
        end=winner.end,
        value=winner.value,
        sources=sources,
        confidence=confidence,
    )


def _select_best_candidate(candidates: list[EntityCandidate]) -> EntityCandidate:
    return sorted(
        candidates,
        key=lambda candidate: (
            -candidate.priority,
            -(candidate.confidence or 0.0),
            -candidate.length,
            candidate.start,
        ),
    )[0]


def _max_confidence(candidates: list[EntityCandidate]) -> float | None:
    confidences = [
        candidate.confidence
        for candidate in candidates
        if candidate.confidence is not None
    ]

    if not confidences:
        return None

    return max(confidences)
