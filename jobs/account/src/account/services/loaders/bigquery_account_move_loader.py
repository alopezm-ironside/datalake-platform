import logging
from typing import Any, Dict, List, Tuple

from etl_common.interfaces.loader_interface import ConnectionInterface, LoaderInterface
from sqlalchemy.orm import Session

from ...models.account_move import AccountMove
from ...models.account_move_line import AccountMoveLine

_logger = logging.getLogger(__name__)


class BigQueryAccountMoveLoader(LoaderInterface, ConnectionInterface):
    """
    Implementación de LoaderInterface para BigQuery usando SQLAlchemy.
    """
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_destination_name(self) -> str:
        return "bigquery"
    
    def load_main_records(self, records: List[Dict[str, Any]]) -> int:
        """Carga movimientos contables."""
        if not records:
            _logger.warning(f"⚠️ [{self.get_destination_name()}] No hay movimientos para cargar")
            return 0
        
        _logger.info(f"💾 [{self.get_destination_name()}] Cargando {len(records)} movimientos...")
        
        try:
            move_objects = [AccountMove(**move) for move in records]
            self.session.bulk_save_objects(move_objects)
            
            _logger.info(f"✅ [{self.get_destination_name()}] {len(records)} movimientos cargados")
            return len(records)
            
        except Exception as e:
            _logger.error(f"❌ [{self.get_destination_name()}] Error cargando movimientos: {e}")
            raise
    
    def load_related_records(self, records: List[Dict[str, Any]]) -> int:
        """Carga líneas de movimientos."""
        if not records:
            _logger.warning(f"⚠️ [{self.get_destination_name()}] No hay líneas para cargar")
            return 0
        
        _logger.info(f"💾 [{self.get_destination_name()}] Cargando {len(records)} líneas...")
        
        try:
            line_objects = [AccountMoveLine(**line) for line in records]
            self.session.bulk_save_objects(line_objects)
            
            _logger.info(f"✅ [{self.get_destination_name()}] {len(records)} líneas cargadas")
            return len(records)
            
        except Exception as e:
            _logger.error(f"❌ [{self.get_destination_name()}] Error cargando líneas: {e}")
            raise
    
    def load_batch_transactional(
        self,
        main_records: List[Dict[str, Any]],
        related_records: List[Dict[str, Any]]
    ) -> Tuple[int, int]:
        """Carga en transacción los movimientos y líneas."""
        _logger.info(f"📦 [{self.get_destination_name()}] Iniciando carga transaccional...")
        _logger.info(f"   Movimientos: {len(main_records)}")
        _logger.info(f"   Líneas: {len(related_records)}")
        
        try:
            moves_count = self.load_main_records(main_records)
            lines_count = self.load_related_records(related_records)
            
            self.commit()
            
            _logger.info(f"✅ [{self.get_destination_name()}] Transacción completada")
            return moves_count, lines_count
            
        except Exception as e:
            _logger.error(f"❌ [{self.get_destination_name()}] Error, haciendo rollback: {e}")
            self.rollback()
            raise
    
    def commit(self):
        """Confirma la transacción."""
        self.session.commit()
    
    def rollback(self):
        """Revierte la transacción."""
        self.session.rollback()
    
    def close(self):
        """Cierra la sesión."""
        self.session.close()