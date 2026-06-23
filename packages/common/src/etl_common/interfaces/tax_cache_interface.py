from abc import ABC, abstractmethod


class TaxCacheInterface(ABC):
    """Interface for caching auxiliary tax information from the source system."""

    @abstractmethod
    def get_tax_rate(self, tax_ids: list[int]) -> float:
        """Return the applicable tax rate for the given tax IDs."""
