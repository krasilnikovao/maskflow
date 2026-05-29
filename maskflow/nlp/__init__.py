"""NLP candidate detection pipeline.

The package is intentionally dependency-light at import time. Concrete
providers load optional NLP libraries only when they are configured and used.
"""

from maskflow.nlp.models import EntityCandidate, ResolvedEntity
from maskflow.nlp.pipeline import NlpPipeline
from maskflow.nlp.providers.base import NlpProvider
from maskflow.nlp.resolver import NlpResolver

__all__ = [
    "EntityCandidate",
    "NlpPipeline",
    "NlpProvider",
    "NlpResolver",
    "ResolvedEntity",
]
