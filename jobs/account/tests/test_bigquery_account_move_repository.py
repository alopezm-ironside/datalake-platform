"""Tests for BigQueryAccountMoveRepository (Phase 5 — Change 2).

All BigQuery/SQLAlchemy I/O is mocked — no real connections.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from account.domain.account_move import AccountMove
from account.domain.account_move_line import AccountMoveLine


def _make_move(move_id: int = 1) -> AccountMove:
    line = AccountMoveLine(
        id=move_id * 10,
        account_move_id=move_id,
        product_id=5,
        description="Product",
        date="2024-01-15",
        quantity=1.0,
        price_unit=100.0,
        discount=0.0,
        price_subtotal=100.0,
        price_total=119.0,
        account_id=42,
        account_name="Sales",
        debit=119.0,
        credit=0.0,
        tax_ids=[1],
        tax_rate=19.0,
        tax_amount=19.0,
    )
    return AccountMove(
        id=move_id,
        name=f"INV/2024/{move_id:04d}",
        move_type="out_invoice",
        date="2024-01-15",
        partner_id=7,
        partner_name="Acme",
        company_id=1,
        company_name="My Co",
        journal_id=3,
        journal_name="Customer Invoices",
        currency_name="CLP",
        amount_untaxed=100.0,
        amount_tax=19.0,
        amount_total=119.0,
        state="posted",
        payment_state="not_paid",
        ref="",
        lines=[line],
    )


def test_save_batch_calls_add_all_and_commit():
    """Repository calls session.add_all then session.commit for a batch."""
    from account.persistence.repositories.bigquery_account_move_repository import (
        BigQueryAccountMoveRepository,
    )

    mock_session = MagicMock()
    mock_connection = MagicMock()
    mock_connection.engine = MagicMock()

    with patch(
        "account.persistence.repositories.bigquery_account_move_repository.Session"
    ) as mock_session_cls:
        mock_session_cls.return_value.__enter__ = lambda s: mock_session
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        repo = BigQueryAccountMoveRepository(
            connection=mock_connection, sync_batch_id="batch-001"
        )
        move = _make_move(1)
        repo.save_batch([move])

    mock_session.add_all.assert_called_once()
    mock_session.commit.assert_called_once()


def test_save_batch_stamps_synced_at_and_sync_batch_id():
    """ORM rows carry synced_at (set by repo) and sync_batch_id; entity unchanged."""
    from account.persistence.repositories.bigquery_account_move_repository import (
        BigQueryAccountMoveRepository,
    )

    captured_rows: list = []
    mock_session = MagicMock()
    mock_session.add_all.side_effect = lambda rows: captured_rows.extend(rows)
    mock_connection = MagicMock()

    with patch(
        "account.persistence.repositories.bigquery_account_move_repository.Session"
    ) as mock_session_cls:
        mock_session_cls.return_value.__enter__ = lambda s: mock_session
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        repo = BigQueryAccountMoveRepository(
            connection=mock_connection, sync_batch_id="batch-42"
        )
        move = _make_move(1)
        original_id = move.id

        repo.save_batch([move])

    # Domain entity not mutated
    assert move.id == original_id
    assert not hasattr(move, "synced_at")

    # ORM rows carry metadata
    orm_moves = [
        r
        for r in captured_rows
        if hasattr(r, "sync_batch_id") and not hasattr(r, "account_move_id")
    ]
    assert orm_moves, "No AccountMove ORM rows in add_all call"
    orm_move = orm_moves[0]
    assert orm_move.sync_batch_id == "batch-42"
    assert isinstance(orm_move.synced_at, datetime)


def test_save_batch_stamps_distinct_synced_at_per_call():
    """Each save_batch stamps a fresh synced_at — two calls yield two distinct
    values, proving the timestamp is taken at write time, not at import time."""
    from account.persistence.repositories.bigquery_account_move_repository import (
        BigQueryAccountMoveRepository,
    )

    captured: list[datetime] = []
    mock_session = MagicMock()
    mock_session.add_all.side_effect = lambda rows: captured.extend(
        r.synced_at for r in rows if not hasattr(r, "account_move_id")
    )

    t1 = datetime(2024, 1, 1, tzinfo=timezone.utc)
    t2 = datetime(2024, 1, 1, 0, 5, tzinfo=timezone.utc)

    with (
        patch(
            "account.persistence.repositories.bigquery_account_move_repository.Session"
        ) as mock_session_cls,
        patch(
            "account.persistence.repositories.bigquery_account_move_repository.datetime"
        ) as mock_dt,
    ):
        mock_session_cls.return_value.__enter__ = lambda s: mock_session
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_dt.now.side_effect = [t1, t2]

        repo = BigQueryAccountMoveRepository(
            connection=MagicMock(), sync_batch_id="batch-A"
        )
        move = _make_move(1)
        repo.save_batch([move])
        repo.save_batch([move])

    assert captured == [t1, t2]


def test_save_batch_append_produces_two_rows_for_same_entity():
    """Calling save_batch twice with the same entity succeeds (append, not upsert)."""
    from account.persistence.repositories.bigquery_account_move_repository import (
        BigQueryAccountMoveRepository,
    )

    add_all_calls: list = []
    mock_session = MagicMock()
    mock_session.add_all.side_effect = lambda rows: add_all_calls.append(list(rows))
    mock_connection = MagicMock()

    with patch(
        "account.persistence.repositories.bigquery_account_move_repository.Session"
    ) as mock_session_cls:
        mock_session_cls.return_value.__enter__ = lambda s: mock_session
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        repo = BigQueryAccountMoveRepository(
            connection=mock_connection, sync_batch_id="batch-B"
        )
        move = _make_move(42)
        repo.save_batch([move])
        repo.save_batch([move])

    assert mock_session.commit.call_count == 2
    assert len(add_all_calls) == 2


def test_save_batch_error_triggers_rollback_and_reraises():
    """On session.commit error: rollback is called and the exception propagates."""
    from account.persistence.repositories.bigquery_account_move_repository import (
        BigQueryAccountMoveRepository,
    )

    mock_session = MagicMock()
    mock_session.commit.side_effect = RuntimeError("BQ write failed")
    mock_connection = MagicMock()

    with patch(
        "account.persistence.repositories.bigquery_account_move_repository.Session"
    ) as mock_session_cls:
        mock_session_cls.return_value.__enter__ = lambda s: mock_session
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        repo = BigQueryAccountMoveRepository(
            connection=mock_connection, sync_batch_id="batch-err"
        )
        with pytest.raises(RuntimeError, match="BQ write failed"):
            repo.save_batch([_make_move(1)])

    mock_session.rollback.assert_called_once()


def test_save_batch_returns_entity_count():
    """save_batch returns entity count (matches RepositoryInterface contract)."""
    from account.persistence.repositories.bigquery_account_move_repository import (
        BigQueryAccountMoveRepository,
    )

    mock_session = MagicMock()
    mock_connection = MagicMock()

    with patch(
        "account.persistence.repositories.bigquery_account_move_repository.Session"
    ) as mock_session_cls:
        mock_session_cls.return_value.__enter__ = lambda s: mock_session
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        repo = BigQueryAccountMoveRepository(
            connection=mock_connection, sync_batch_id="batch-count"
        )
        result = repo.save_batch([_make_move(1), _make_move(2)])

    assert result == 2
