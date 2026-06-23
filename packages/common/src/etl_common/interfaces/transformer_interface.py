"""Transformer port — converts raw source dicts into typed domain entities.

A single transform() method replaces the old dict-tuple API. Validation
is a private concern of each concrete transformer, not a public interface.
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class TransformerInterface(ABC, Generic[T]):
    """Abstract transformer: raw source dicts → typed domain entities.

    The SyncPipeline calls transform(raw_batch) once per batch and passes
    the resulting list[T] directly to RepositoryInterface.save_batch().
    """

    @abstractmethod
    def transform(self, raw_batch: list[dict[str, Any]]) -> list[T]:
        """Transform a batch of raw source records into domain entities.

        Args:
            raw_batch: List of raw dicts from the extractor.

        Returns:
            List of typed domain entities (not dicts).
        """
