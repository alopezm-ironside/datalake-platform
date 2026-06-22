import logging
import uuid
from typing import List, Optional

from etl_common.conf.settings import Settings
from etl_common.infrastructure.bigquery_connection import BigQueryConnection
from etl_common.infrastructure.odoo_manager import OdooManager
from etl_common.interfaces.extractor_interface import ExtractorInterface
from etl_common.interfaces.loader_interface import LoaderInterface
from etl_common.interfaces.sync_app_interface import SyncAppInterface
from etl_common.interfaces.transformer_interface import TransformerInterface
from etl_common.utils.sync_tracker import SyncTracker
from sqlalchemy.orm import Session

from ..factories.service_factory import ServiceFactory

logger = logging.getLogger(__name__)


class AccountMoveApp(SyncAppInterface):
    """
    Aplicación principal para sincronización de movimientos contables.
    """

    def __init__(
        self,
        settings: Optional[Settings] = None,
        extractor: Optional[ExtractorInterface] = None,
        transformer: Optional[TransformerInterface] = None,
        loader: Optional[LoaderInterface] = None,
    ):
        # Settings se resuelve de forma diferida para no exigir variables de
        # entorno al importar el módulo (p. ej. durante la compilación de bytecode).
        self.settings = settings or Settings()

        # Configuración
        self.BATCH_SIZE = 1000

        # Services inyectados (pueden ser None)
        self._extractor = extractor
        self._transformer = transformer
        self._loader = loader

        # Managers
        self.odoo_manager = None
        self.bq_connection = None
        self.sync_tracker = None

    def get_module_name(self) -> str:
        return "accounting"

    def _initialize_services(self, session: Session, sync_batch_id: str):
        """
        Inicializa servicios.

        Si se inyectaron servicios (testing), los usa.
        Si no, crea servicios usando Factory (producción).
        """
        logger.info("🛠️  Inicializando servicios...")

        # Extractor
        if self._extractor is None:
            self._extractor = ServiceFactory.create_extractor(
                source_type="odoo", odoo_manager=self.odoo_manager
            )
        else:
            logger.info("✓ Usando extractor inyectado (probablemente test)")

        # Transformer
        if self._transformer is None:
            self._transformer = ServiceFactory.create_transformer(
                extractor=self._extractor, sync_batch_id=sync_batch_id
            )
        else:
            logger.info("✓ Usando transformer inyectado (probablemente test)")

        # Loader
        if self._loader is None:
            self._loader = ServiceFactory.create_loader(
                destination_type="bigquery", session=session
            )
        else:
            logger.info("✓ Usando loader inyectado (probablemente test)")

        # Tracker
        self.sync_tracker = SyncTracker(session, self.get_module_name())

        logger.info("✅ Servicios inicializados\n")

    def _connect_dependencies(self):
        """Conecta a sistemas externos (Odoo, BigQuery)."""
        logger.info("🔗 Conectando a Odoo...")
        self.odoo_manager = OdooManager()
        self.odoo_manager.connect()
        logger.info("✅ Conectado a Odoo\n")

        logger.info("🔗 Conectando a BigQuery...")
        self.bq_connection = BigQueryConnection(
            project_id=self.settings.GOOGLE_PROJECT_ID,
            credentials=self.settings.GOOGLE_CREDENTIAL_SERVICE_FILE,
            location=self.settings.GOOGLE_LOCATION,
        )

        self.bq_connection.create_dataset_if_not_exists(
            self.settings.BQ_DATASET_RAW, description="Raw data from Odoo ERP"
        )
        self.bq_connection.create_dataset_if_not_exists(
            self.settings.BQ_DATASET_CONTROL, description="Sync control and metadata"
        )

        self.bq_connection.create_tables()
        logger.info("✅ Conectado a BigQuery\n")

    def _process_batch(
        self, move_ids: List[int], batch_num: int, total_batches: int
    ) -> tuple[int, int]:
        """
        Procesa un batch: Extrae → Transforma → Carga.
        """
        logger.info(
            f"📦 Procesando batch {batch_num}/{total_batches} ({len(move_ids)} movimientos)"
        )

        # EXTRACCIÓN
        raw_data = self._extractor.fetch_batch(move_ids)
        self.sync_tracker.update_stats(odoo_api_calls=1)

        # TRANSFORMACIÓN
        transformed_moves, transformed_lines = self._transformer.transform_batch(
            raw_data
        )

        # CARGA
        moves_count, lines_count = self._loader.load_batch_transactional(
            transformed_moves, transformed_lines
        )

        self.sync_tracker.update_stats(
            records_processed=len(move_ids), records_inserted=moves_count
        )

        logger.info(
            f"✅ Batch {batch_num} completado: {moves_count} movimientos, {lines_count} líneas\n"
        )

        return moves_count, lines_count

    def run(self):
        """Ejecuta el proceso de sincronización completo."""
        session = None

        try:
            logger.info("=" * 60)
            logger.info("📊 SINCRONIZACIÓN DE MOVIMIENTOS CONTABLES")
            logger.info("=" * 60 + "\n")

            # 1. Conectar
            self._connect_dependencies()

            # 2. Crear sesión
            session = Session(bind=self.bq_connection.engine)

            # 3. Inicializar servicios (Factory o Inyectados)
            sync_batch_id = str(uuid.uuid4())
            self._initialize_services(session, sync_batch_id)

            # 4. Obtener watermark
            last_processed_id = self.bq_connection.get_last_sync_watermark(
                self.get_module_name(), self.settings.BQ_DATASET_CONTROL
            )
            logger.info(f"📍 Último ID procesado: {last_processed_id}\n")

            # 5. Iniciar tracking
            self.sync_tracker.start(sync_type="incremental")

            # 6. Obtener IDs nuevos
            new_move_ids = self._extractor.fetch_new_ids(last_processed_id)

            if not new_move_ids:
                logger.info("✅ No hay movimientos nuevos para sincronizar\n")
                self.sync_tracker.finish("success", last_processed_id)
                return

            total_moves = len(new_move_ids)
            logger.info(f"📋 Total de movimientos a procesar: {total_moves}\n")

            # 7. Procesar en batches
            total_batches = (total_moves + self.BATCH_SIZE - 1) // self.BATCH_SIZE

            for batch_num in range(1, total_batches + 1):
                start_idx = (batch_num - 1) * self.BATCH_SIZE
                end_idx = min(start_idx + self.BATCH_SIZE, total_moves)

                batch_ids = new_move_ids[start_idx:end_idx]

                self._process_batch(batch_ids, batch_num, total_batches)

            # 8. Finalizar
            final_id = new_move_ids[-1]
            self.sync_tracker.finish("success", final_id)

            logger.info("=" * 60)
            logger.info("✅ SINCRONIZACIÓN COMPLETADA EXITOSAMENTE")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"❌ Error crítico en sincronización: {e}")
            if self.sync_tracker:
                self.sync_tracker.finish("failed", last_processed_id or 0, str(e))
            raise

        finally:
            if session:
                session.close()

