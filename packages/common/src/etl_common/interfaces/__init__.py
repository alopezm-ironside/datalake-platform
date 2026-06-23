"""etl_common.interfaces — public port contracts.

Existing interfaces (LoaderInterface, SyncAppInterface) are preserved until
Change 3 removes them.  New ports (RepositoryInterface, SyncStateInterface,
SyncStats) are added alongside.
"""

from etl_common.interfaces.extractor_interface import (
    ExtractorInterface,
    TaxCacheInterface,
)
from etl_common.interfaces.loader_interface import ConnectionInterface, LoaderInterface
from etl_common.interfaces.repository_interface import RepositoryInterface
from etl_common.interfaces.sync_app_interface import SyncAppInterface
from etl_common.interfaces.sync_state_interface import SyncStateInterface, SyncStats
from etl_common.interfaces.transformer_interface import (
    TransformerInterface,
    ValidationInterface,
)

__all__ = [
    # Existing — kept for backward compatibility until Change 3
    "ConnectionInterface",
    "ExtractorInterface",
    "LoaderInterface",
    "RepositoryInterface",
    "SyncAppInterface",
    "SyncStateInterface",
    "SyncStats",
    "TaxCacheInterface",
    "TransformerInterface",
    "ValidationInterface",
]
