import logging

from google.cloud import bigquery
from sqlalchemy import create_engine

from ..core.base import Base
from ..core.singleton_meta import SingletonMeta

_logger = logging.getLogger(__name__)


class BigQueryConnection(metaclass=SingletonMeta):
    def __init__(self, credentials: str, project_id: str, location: str):
        self.credentials = credentials
        self.project_id = project_id
        self.location = location
        self.bq_client = bigquery.Client(project=self.project_id, location=self.location,)
        self.engine = create_engine(
            f'bigquery://{self.project_id}',
            connect_args={'client': self.bq_client},
            credentials_path=self.credentials
        )
        self.connection = self.engine.connect()

    def create_dataset_if_not_exists(self, dataset_id: str, description: str = ""):
        """Crea un dataset en BigQuery si no existe."""
        dataset_ref = f"{self.project_id}.{dataset_id}"

        try:
            self.bq_client.get_dataset(dataset_ref)
            _logger.info(f"📦 Dataset ya existe: {dataset_id}")
        except Exception:
            dataset = bigquery.Dataset(dataset_ref)
            dataset.description = description

            dataset = self.bq_client.create_dataset(dataset, timeout=30)
            _logger.info(f"✅ Dataset creado: {dataset_id}")

    def create_tables(self):
        """
        Crea las tablas definidas en los modelos si no existen.
        """
        _logger.info("🛠️  Verificando/Creando tablas en BigQuery...")
        try:
            Base.metadata.create_all(self.engine, checkfirst=True)
            _logger.info("✅ Tablas base creadas en BigQuery")

        except Exception as e:
            _logger.error(f"❌ Error al crear tablas en BigQuery: {e}")
            raise

    def get_last_sync_watermark(self, module_name: str, dataset_id: str) -> int:
        """Obtiene el último ID sincronizado exitosamente."""
        query = f"""
        SELECT MAX(last_processed_id) as watermark
        FROM `{self.project_id}.{dataset_id}.sync_metadata`
        WHERE module_name = @module_name
          AND status = 'success'
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("module_name", "STRING", module_name)
            ]
        )

        try:
            query_job = self.bq_client.query(query, job_config=job_config)
            results = list(query_job.result())

            if results and results[0].watermark:
                return results[0].watermark
            return 0

        except Exception as e:
            _logger.warning(f"⚠️ Error obteniendo watermark: {e}")
            return 0
