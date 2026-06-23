"""Transformer port — converts raw source dicts into typed domain entities.

The old dict-tuple API (transform_record / transform_related_records /
transform_batch) is replaced by a single transform() method that returns
a typed list of domain entities. Validation logic moves to the concrete
transformer as a private method.

Concrete implementations are updated in Change 1 → Phase 6 (jobs/account).
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


class ValidationInterface(ABC):
    """Interface para validación de datos transformados."""

    @abstractmethod
    def validate(self, data: dict[str, Any]) -> bool:
        """Valida que un registro cumpla reglas de negocio."""
