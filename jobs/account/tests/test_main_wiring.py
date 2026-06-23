"""Smoke test: account/__main__.main() wires SyncPipeline and calls run().

The crash-between-batch reprocess invariant is fully proven at the pipeline
level in packages/common/tests/test_sync_pipeline.py
(test_crash_between_save_batch_and_checkpoint_causes_reprocess). That test
covers the effectively-once guarantee in isolation from any specific adapter.

This test verifies the composition root wires the pipeline correctly — it
mocks all external I/O boundaries and asserts that SyncPipeline.run() is
reached without import errors or wiring mistakes.
"""

from unittest.mock import MagicMock, patch


def _mock_settings() -> MagicMock:
    mock = MagicMock()
    mock.ODOO_URL = "http://odoo"
    mock.ODOO_DB = "db"
    mock.ODOO_USER = "user"
    mock.ODOO_PASSWORD = "pass"
    mock.GOOGLE_PROJECT_ID = "proj"
    mock.GOOGLE_CREDENTIAL_SERVICE_FILE = "/creds.json"
    mock.GOOGLE_LOCATION = "us-central1"
    mock.BQ_DATASET_RAW = "odoo_raw"
    mock.BQ_DATASET_CONTROL = "control"
    mock.LOG_BACKEND = "gcp"
    mock.BATCH_SIZE = 1000
    return mock


def test_main_wires_pipeline_and_calls_run() -> None:
    """main() must reach SyncPipeline.run() when all I/O is mocked."""
    mock_pipeline = MagicMock()

    with (
        patch("account.__main__.Settings", return_value=_mock_settings()),
        patch("account.__main__.configure_logging"),
        patch("account.__main__.resolve_backend"),
        patch("account.__main__.OdooManager") as mock_odoo_cls,
        patch("account.__main__.BigQueryConnection") as mock_bq_cls,
        patch("account.__main__.OdooAccountMoveExtractor") as mock_extractor_cls,
        patch("account.__main__.AccountMoveTransformer") as mock_transformer_cls,
        patch("account.__main__.BigQueryAccountMoveRepository") as mock_repo_cls,
        patch("account.__main__.BigQuerySyncState") as mock_state_cls,
        patch("account.__main__.SyncPipeline", return_value=mock_pipeline),
    ):
        mock_odoo_cls.return_value = MagicMock()
        mock_bq_cls.return_value = MagicMock()
        mock_extractor_cls.return_value = MagicMock()
        mock_transformer_cls.return_value = MagicMock()
        mock_repo_cls.return_value = MagicMock()
        mock_state_cls.return_value = MagicMock()

        from account.__main__ import main

        main()

    mock_pipeline.run.assert_called_once()


def test_main_calls_configure_logging_before_adapters() -> None:
    """configure_logging() must be called before any adapter is constructed."""
    call_order: list[str] = []

    def record(name: str):
        def side_effect(*_a: object, **_kw: object) -> MagicMock:
            call_order.append(name)
            return MagicMock()

        return side_effect

    mock_pipeline = MagicMock()

    with (
        patch("account.__main__.Settings", return_value=_mock_settings()),
        patch(
            "account.__main__.configure_logging",
            side_effect=lambda _b: call_order.append("configure_logging"),
        ),
        patch("account.__main__.resolve_backend", return_value=MagicMock()),
        patch("account.__main__.OdooManager", side_effect=record("OdooManager")),
        patch(
            "account.__main__.BigQueryConnection",
            side_effect=record("BigQueryConnection"),
        ),
        patch(
            "account.__main__.OdooAccountMoveExtractor",
            side_effect=record("OdooAccountMoveExtractor"),
        ),
        patch(
            "account.__main__.AccountMoveTransformer",
            side_effect=record("AccountMoveTransformer"),
        ),
        patch(
            "account.__main__.BigQueryAccountMoveRepository",
            side_effect=record("BigQueryAccountMoveRepository"),
        ),
        patch(
            "account.__main__.BigQuerySyncState",
            side_effect=record("BigQuerySyncState"),
        ),
        patch("account.__main__.SyncPipeline", return_value=mock_pipeline),
    ):
        from account.__main__ import main

        main()

    assert call_order[0] == "configure_logging", (
        f"configure_logging must be first adapter call, got: {call_order}"
    )
