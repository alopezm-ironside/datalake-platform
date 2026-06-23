"""Assert BigQueryConnection wires schema_translate_map from dataset params.

No real BigQuery connection — the engine construction is patched.
"""

from unittest.mock import MagicMock, patch


def _make_mock_engine(schema_translate_map: dict) -> MagicMock:
    engine = MagicMock()
    engine.execution_options.return_value = engine
    engine._execution_options = schema_translate_map
    return engine


def test_bigquery_connection_sets_schema_translate_map() -> None:
    """BigQueryConnection must call execution_options with the dataset map."""
    from etl_common.infrastructure.bigquery_connection import BigQueryConnection

    fake_engine = MagicMock()
    fake_engine.execution_options.return_value = fake_engine

    with (
        patch(
            "etl_common.infrastructure.bigquery_connection.bigquery.Client"
        ) as mock_bq_client,
        patch(
            "etl_common.infrastructure.bigquery_connection.create_engine",
            return_value=fake_engine,
        ),
    ):
        mock_bq_client.return_value = MagicMock()
        conn = BigQueryConnection(
            project_id="my-project",
            credentials="/creds.json",
            location="us-central1",
            raw_dataset="datalake_odoo_raw",
            control_dataset="datalake_control",
        )

    fake_engine.execution_options.assert_called_once_with(
        schema_translate_map={"raw": "datalake_odoo_raw", "control": "datalake_control"}
    )
    assert conn.engine is fake_engine


def test_bigquery_connection_has_no_create_dataset_method() -> None:
    """create_dataset_if_not_exists must be removed — datasets are IaC-owned."""
    from etl_common.infrastructure.bigquery_connection import BigQueryConnection

    assert not hasattr(BigQueryConnection, "create_dataset_if_not_exists"), (
        "create_dataset_if_not_exists must be removed; IaC owns datasets"
    )


def test_bigquery_connection_init_accepts_dataset_params() -> None:
    """__init__ must accept raw_dataset and control_dataset keyword args."""
    import inspect

    from etl_common.infrastructure.bigquery_connection import BigQueryConnection

    sig = inspect.signature(BigQueryConnection.__init__)
    params = set(sig.parameters)
    assert "raw_dataset" in params, "raw_dataset param missing from __init__"
    assert "control_dataset" in params, "control_dataset param missing from __init__"
