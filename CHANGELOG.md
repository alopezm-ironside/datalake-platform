## Unreleased

### Feat

- **account**: wire LOG_BACKEND setting and migrate composition root to resolve_backend
- **account**: make pipeline batch size configurable via BATCH_SIZE env
- **account**: wire composition root, apply observability, add wiring tests
- **account**: add persistence layer — ORM models, BigQueryAccountMoveRepository, BigQuerySyncState
- **account**: add AccountMove aggregate root and AccountMoveLine domain entities
- **etl_common**: add structured JSON logging module — ADR-8 observability
- **etl_common**: add generic SyncPipeline with invariant run() loop
- **etl_common**: add RepositoryInterface[T], SyncStateInterface, and SyncStats ports
- **account**: add account.move to BigQuery ETL Cloud Run Job
- **common**: add shared ETL contracts and infrastructure

### Fix

- **account**: fail loud when sync_batch_id is unbound in save_batch
- **account**: add TYPE_CHECKING imports for ORM forward references; remove stale noqa directives
- **etl_common**: harden SyncPipeline watermark, failed-run progress and batch stats

### Refactor

- **common**: replace stdlib logging with structlog structured events in infra/utils
- **account**: migrate get_logger imports to etl_common.observability generic module
- **observability**: extract pluggable LogBackend port with GCP and console adapters
- **common**: type core, utils, and infra modules to mypy strict
- **common**: slim BigQueryConnection to pure connection/DDL helper
- **account**: remove old cluster and superseded etl_common interfaces
- **account**: type and clean the Odoo extractor, finish TaxCacheInterface split
- **account**: rewrite AccountMoveTransformer with transform() API; split TaxCacheInterface; remove ValidationInterface
- **etl_common**: split SyncStats into its own file for discoverability
- **etl_common**: rename logging module to gcp_logging and own the GCP coupling
- **etl_common**: trim non-essential comments in logging module
