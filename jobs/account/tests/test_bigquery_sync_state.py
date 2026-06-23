"""Tests for BigQuerySyncState (Phase 5 — Change 2).

All BigQuery/SQLAlchemy I/O is mocked — no real connections.
"""

from unittest.mock import MagicMock, patch

from etl_common.interfaces.sync_stats import SyncStats


def _make_connection() -> MagicMock:
    conn = MagicMock()
    conn.engine = MagicMock()
    return conn


def test_get_watermark_returns_last_processed_id_from_success_run():
    """get_watermark returns last_processed_id from the most recent success run."""
    from account.persistence.repositories.bigquery_sync_state import BigQuerySyncState

    mock_session = MagicMock()
    mock_row = MagicMock()
    mock_row.last_processed_id = 500
    query_chain = mock_session.query.return_value.filter.return_value
    query_chain.filter.return_value.order_by.return_value.first.return_value = mock_row

    with patch(
        "account.persistence.repositories.bigquery_sync_state.Session"
    ) as mock_session_cls:
        mock_session_cls.return_value.__enter__ = lambda s: mock_session
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        state = BigQuerySyncState(
            connection=_make_connection(), control_dataset="control"
        )
        result = state.get_watermark("accounting")

    assert result == 500
    status_clause = query_chain.filter.call_args[0][0]
    assert "status" in str(status_clause)
    assert status_clause.right.value == "success"


def test_get_watermark_returns_zero_when_no_success_run():
    """get_watermark returns 0 if there is no prior success run."""
    from account.persistence.repositories.bigquery_sync_state import BigQuerySyncState

    mock_session = MagicMock()
    query_chain = mock_session.query.return_value.filter.return_value
    query_chain.filter.return_value.order_by.return_value.first.return_value = None

    with patch(
        "account.persistence.repositories.bigquery_sync_state.Session"
    ) as mock_session_cls:
        mock_session_cls.return_value.__enter__ = lambda s: mock_session
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        state = BigQuerySyncState(
            connection=_make_connection(), control_dataset="control"
        )
        result = state.get_watermark("accounting")

    assert result == 0


def test_start_inserts_running_row_and_returns_sync_batch_id():
    """start() inserts a sync_metadata row with status=running and returns unique id."""
    from account.persistence.repositories.bigquery_sync_state import BigQuerySyncState

    added_rows: list = []
    mock_session = MagicMock()
    mock_session.add.side_effect = lambda row: added_rows.append(row)

    with patch(
        "account.persistence.repositories.bigquery_sync_state.Session"
    ) as mock_session_cls:
        mock_session_cls.return_value.__enter__ = lambda s: mock_session
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        state = BigQuerySyncState(
            connection=_make_connection(), control_dataset="control"
        )
        batch_id = state.start("accounting")

    assert batch_id
    assert len(added_rows) == 1
    row = added_rows[0]
    assert row.status == "running"
    assert row.module_name == "accounting"
    assert row.sync_id == batch_id


def test_start_returns_unique_ids():
    """Two consecutive start() calls produce different sync_batch_ids."""
    from account.persistence.repositories.bigquery_sync_state import BigQuerySyncState

    mock_session = MagicMock()

    with patch(
        "account.persistence.repositories.bigquery_sync_state.Session"
    ) as mock_session_cls:
        mock_session_cls.return_value.__enter__ = lambda s: mock_session
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        state = BigQuerySyncState(
            connection=_make_connection(), control_dataset="control"
        )
        id1 = state.start("accounting")
        id2 = state.start("accounting")

    assert id1 != id2


def test_checkpoint_updates_run_row_in_place():
    """checkpoint() UPDATEs the run row in place, advancing last_processed_id."""
    from account.persistence.repositories.bigquery_sync_state import BigQuerySyncState

    mock_session = MagicMock()
    stats = SyncStats(
        records_processed=100, records_inserted=98, records_failed=2, source_api_calls=1
    )

    with patch(
        "account.persistence.repositories.bigquery_sync_state.Session"
    ) as mock_session_cls:
        mock_session_cls.return_value.__enter__ = lambda s: mock_session
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        state = BigQuerySyncState(
            connection=_make_connection(), control_dataset="control"
        )
        state.checkpoint("batch-001", last_processed_id=500, stats=stats)

    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()


def test_finish_updates_row_with_success_status():
    """finish() calls session.execute to UPDATE the row with status=success."""
    from account.persistence.repositories.bigquery_sync_state import BigQuerySyncState

    mock_session = MagicMock()

    with patch(
        "account.persistence.repositories.bigquery_sync_state.Session"
    ) as mock_session_cls:
        mock_session_cls.return_value.__enter__ = lambda s: mock_session
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        state = BigQuerySyncState(
            connection=_make_connection(), control_dataset="control"
        )
        state.finish("batch-001", "success", last_processed_id=1000)

    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()
