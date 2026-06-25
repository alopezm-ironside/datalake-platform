"""Composition root for the account ETL Cloud Run Job.

Exposed as the `account-job` console script (see pyproject.toml) and invoked
directly by the container ENTRYPOINT.
"""

from etl_common.conf.settings import Settings
from etl_common.infrastructure.bigquery_connection import BigQueryConnection
from etl_common.infrastructure.odoo_manager import OdooManager
from etl_common.observability import configure_logging, resolve_backend
from etl_common.sync_pipeline import SyncPipeline

from account.persistence.repositories.bigquery_account_move_repository import (
    BigQueryAccountMoveRepository,
)
from account.persistence.repositories.bigquery_sync_state import BigQuerySyncState
from account.services.extractors.odoo_account_move_extractor import (
    OdooAccountMoveExtractor,
)
from account.services.transformers.account_move_transformer import (
    AccountMoveTransformer,
)


def main() -> None:
    settings = Settings()
    configure_logging(resolve_backend(settings.LOG_BACKEND))

    odoo = OdooManager(
        url=settings.ODOO_URL,
        db=settings.ODOO_DB,
        user=settings.ODOO_USER,
        password=settings.ODOO_PASSWORD,
    )
    odoo.connect()

    connection = BigQueryConnection(
        project_id=settings.GOOGLE_PROJECT_ID,
        credentials=settings.GOOGLE_CREDENTIAL_SERVICE_FILE,
        location=settings.GOOGLE_LOCATION,
        raw_dataset=settings.BQ_DATASET_RAW,
        control_dataset=settings.BQ_DATASET_CONTROL,
    )
    connection.create_tables()

    extractor = OdooAccountMoveExtractor(odoo, extract_limit=settings.EXTRACT_LIMIT)
    transformer = AccountMoveTransformer(extractor)
    repository = BigQueryAccountMoveRepository(connection)
    sync_state = BigQuerySyncState(connection)

    SyncPipeline(
        module_name="accounting",
        extractor=extractor,
        transformer=transformer,
        repository=repository,
        sync_state=sync_state,
        batch_size=settings.BATCH_SIZE,
    ).run()


if __name__ == "__main__":
    main()
