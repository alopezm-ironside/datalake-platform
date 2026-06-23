"""etl_common.interfaces — public port contracts."""

from etl_common.interfaces.extractor_interface import ExtractorInterface
from etl_common.interfaces.repository_interface import RepositoryInterface
from etl_common.interfaces.sync_state_interface import SyncStateInterface
from etl_common.interfaces.sync_stats import SyncStats
from etl_common.interfaces.tax_cache_interface import TaxCacheInterface
from etl_common.interfaces.transformer_interface import TransformerInterface

__all__ = [
    "ExtractorInterface",
    "RepositoryInterface",
    "SyncStateInterface",
    "SyncStats",
    "TaxCacheInterface",
    "TransformerInterface",
]
