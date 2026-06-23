"""Generic append-only repository port.

All sink adapters (BigQuery, Snowflake, Postgres, …) must implement this
interface. The pipeline depends only on this port — it never imports any
concrete adapter or ORM type.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class RepositoryInterface(ABC, Generic[T]):
    """Abstract append-only repository for domain entities of type T.

    Contract:
    - save_batch appends all entities in a single operation.
    - No upsert or MERGE semantics: re-calling with the same entities
      produces additional Bronze versions with different metadata columns.
    - The method returns the number of entities persisted.
    - On error the implementation must rollback and re-raise.
    """

    @abstractmethod
    def save_batch(self, entities: list[T]) -> int:
        """Append entities to the sink and commit.

        Args:
            entities: Domain entities to persist (typed list[T]).

        Returns:
            Number of entities successfully persisted.

        Raises:
            Exception: Any sink-level error after rollback.
        """
