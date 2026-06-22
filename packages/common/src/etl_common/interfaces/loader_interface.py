from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple


class LoaderInterface(ABC):
    """
    Interface para servicios de carga de datos.

    Cualquier implementación (BigQuery, Postgres, Snowflake, etc.) debe cumplir este contrato.
    """

    @abstractmethod
    def load_main_records(self, records: List[Dict[str, Any]]) -> int:
        """
        Carga registros principales (ej: movimientos contables).

        Args:
            records: Lista de registros transformados

        Returns:
            Número de registros insertados exitosamente
        """
        pass

    @abstractmethod
    def load_related_records(self, records: List[Dict[str, Any]]) -> int:
        """
        Carga registros relacionados (ej: líneas de movimientos).

        Args:
            records: Lista de registros relacionados transformados

        Returns:
            Número de registros insertados exitosamente
        """
        pass

    @abstractmethod
    def load_batch_transactional(
        self,
        main_records: List[Dict[str, Any]],
        related_records: List[Dict[str, Any]]
    ) -> Tuple[int, int]:
        """
        Carga registros principales y relacionados en una transacción atómica.

        Args:
            main_records: Registros principales
            related_records: Registros relacionados

        Returns:
            Tupla (main_count, related_count)
        """
        pass

    @abstractmethod
    def get_destination_name(self) -> str:
        """
        Retorna el nombre del sistema destino.

        Returns:
            Nombre identificador del destino (ej: 'bigquery', 'postgres')
        """
        pass


class ConnectionInterface(ABC):
    """Interface para manejo de conexiones al destino."""

    @abstractmethod
    def commit(self):
        """Confirma la transacción actual."""
        pass

    @abstractmethod
    def rollback(self):
        """Revierte la transacción actual."""
        pass

    @abstractmethod
    def close(self):
        """Cierra la conexión."""
        pass
