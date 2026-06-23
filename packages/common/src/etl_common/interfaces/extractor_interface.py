from abc import ABC, abstractmethod
from typing import Any


class ExtractorInterface(ABC):
    """
    Interface para servicios de extracción de datos.

    Cualquier implementación (Odoo, SAP, API REST, CSV, etc.) debe cumplir el contrato.
    """

    @abstractmethod
    def fetch_new_ids(self, last_processed_id: int = 0) -> list[int]:
        """
        Obtiene IDs de registros nuevos desde el último procesado.

        Args:
            last_processed_id: Último ID procesado en sincronización anterior

        Returns:
            Lista de IDs ordenados ascendentemente
        """
        pass

    @abstractmethod
    def fetch_batch(self, ids: list[int]) -> list[dict[str, Any]]:
        """
        Obtiene datos completos de un batch de registros.

        Args:
            ids: Lista de IDs a obtener

        Returns:
            Lista de diccionarios con datos raw del sistema fuente
        """
        pass

    @abstractmethod
    def get_source_name(self) -> str:
        """
        Retorna el nombre del sistema fuente.

        Returns:
            Nombre identificador del sistema (ej: 'odoo', 'sap', 'api')
        """
        pass


class TaxCacheInterface(ABC):
    """Interface para cachear información auxiliar (como impuestos)."""

    @abstractmethod
    def get_tax_rate(self, tax_ids: list[int]) -> float:
        """Obtiene la tasa de impuesto."""
        pass
