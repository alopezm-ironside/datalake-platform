"""etl_common.interfaces — public port contracts.

LoaderInterface and SyncAppInterface are preserved until Change 3 removes them.
ValidationInterface is removed (validation is a private concern of each transformer).
TaxCacheInterface is now in its own file for discoverability.
"""

from etl_common.interfaces.extractor_interface import ExtractorInterface
from etl_common.interfaces.loader_interface import ConnectionInterface, LoaderInterface
from etl_common.interfaces.repository_interface import RepositoryInterface
from etl_common.interfaces.sync_app_interface import SyncAppInterface
from etl_common.interfaces.sync_state_interface import SyncStateInterface
from etl_common.interfaces.sync_stats import SyncStats
from etl_common.interfaces.tax_cache_interface import TaxCacheInterface
from etl_common.interfaces.transformer_interface import TransformerInterface

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
]
