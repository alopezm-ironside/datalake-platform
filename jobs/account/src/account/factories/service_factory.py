import logging

from etl_common.infrastructure.odoo_manager import OdooManager
from etl_common.interfaces.extractor_interface import ExtractorInterface
from etl_common.interfaces.loader_interface import LoaderInterface
from etl_common.interfaces.transformer_interface import TransformerInterface
from sqlalchemy.orm import Session

from ..services.extractors.odoo_account_move_extractor import OdooAccountMoveExtractor
from ..services.loaders.bigquery_account_move_loader import BigQueryAccountMoveLoader
from ..services.transformers.account_move_transformer import AccountMoveTransformer

logger = logging.getLogger(__name__)


class ServiceFactory:
    """Factory para crear servicios de sincronización."""
    
    @staticmethod
    def create_extractor(
        source_type: str,
        odoo_manager: OdooManager = None
    ) -> ExtractorInterface:
        """
        Crea un extractor según el tipo de fuente.
        
        Args:
            source_type: Tipo de fuente ('odoo', 'sap', 'api', etc.)
            odoo_manager: Manager de Odoo (solo si source_type='odoo')
        
        Returns:
            Implementación de ExtractorInterface
        """
        if source_type.lower() == 'odoo':
            if odoo_manager is None:
                raise ValueError("OdooManager es requerido para source_type='odoo'")
            logger.info("🏭 Factory: Creando OdooAccountMoveExtractor")
            return OdooAccountMoveExtractor(odoo_manager)
        
        # En caso de agregar más fuentes, aquí es donde se agregarían más condiciones
        
        else:
            raise ValueError(f"Tipo de fuente no soportado: {source_type}")
    
    @staticmethod
    def create_transformer(
        extractor: ExtractorInterface,
        sync_batch_id: str
    ) -> TransformerInterface:
        """
        Crea un transformer para movimientos contables.
        
        Args:
            extractor: Extractor que implementa TaxCacheInterface
            sync_batch_id: ID del batch de sincronización
        
        Returns:
            Implementación de TransformerInterface
        """
        logger.info("🏭 Factory: Creando AccountMoveTransformer")
        return AccountMoveTransformer(extractor, sync_batch_id)
    
    @staticmethod
    def create_loader(
        destination_type: str,
        session: Session
    ) -> LoaderInterface:
        """
        Crea un loader según el tipo de destino.
        
        Args:
            destination_type: Tipo de destino ('bigquery', 'postgres', 'snowflake', etc.)
            session: Sesión de SQLAlchemy
        
        Returns:
            Implementación de LoaderInterface
        """
        if destination_type.lower() == 'bigquery':
            logger.info("🏭 Factory: Creando BigQueryAccountingLoader")
            return BigQueryAccountMoveLoader(session)
        
        # En caso de más destinos, aquí se agregarían más condiciones
        
        else:
            raise ValueError(f"Tipo de destino no soportado: {destination_type}")