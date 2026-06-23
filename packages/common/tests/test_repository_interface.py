"""Tests for RepositoryInterface[T] — verify abstract contract enforcement."""

import pytest
from etl_common.interfaces import RepositoryInterface


class ConcreteRepository(RepositoryInterface[int]):
    """Minimal valid concrete subclass."""

    def save_batch(self, entities: list[int]) -> int:
        return len(entities)


class IncompleteRepository(RepositoryInterface[int]):
    """Subclass that does NOT implement save_batch."""


def test_repository_interface_is_abstract() -> None:
    """Subclassing without save_batch raises TypeError on instantiation."""
    with pytest.raises(TypeError):
        IncompleteRepository()  # type: ignore[abstract]


def test_repository_interface_can_be_subclassed() -> None:
    """A complete implementation can be instantiated."""
    repo = ConcreteRepository()
    assert isinstance(repo, RepositoryInterface)


def test_save_batch_returns_count() -> None:
    """save_batch returns the number of entities persisted."""
    repo = ConcreteRepository()
    result = repo.save_batch([1, 2, 3])
    assert result == 3


def test_save_batch_empty_list() -> None:
    """save_batch with empty list returns 0."""
    repo = ConcreteRepository()
    result = repo.save_batch([])
    assert result == 0
