"""Reserved module.

The Match type now lives in :mod:`maskflow.core.types`. Re-exported here for
backwards compatibility with any external code that may have imported it from
this location previously.
"""

from maskflow.core.types import Match

__all__ = ["Match"]
