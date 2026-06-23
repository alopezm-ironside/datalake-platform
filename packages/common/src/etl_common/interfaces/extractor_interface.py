from abc import ABC, abstractmethod
from typing import Any

from etl_common.interfaces.tax_cache_interface import TaxCacheInterface


class ExtractorInterface(ABC):
    """Interface for source data extraction adapters (Odoo, SAP, REST API, CSV…)."""

    @abstractmethod
    def fetch_new_ids(self, last_processed_id: int = 0) -> list[int]:
        """Return IDs of new records since last_processed_id, ascending."""

    @abstractmethod
    def fetch_batch(self, ids: list[int]) -> list[dict[str, Any]]:
        """Return raw source records for the given IDs."""

    @abstractmethod
    def get_source_name(self) -> str:
        """Return a short identifier for the source system (e.g. 'odoo')."""


__all__ = ["ExtractorInterface", "TaxCacheInterface"]
