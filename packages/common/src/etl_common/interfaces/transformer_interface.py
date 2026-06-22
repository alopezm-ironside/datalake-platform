from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple


class TransformerInterface(ABC):
    """
    Interface para servicios de transformación de datos.

    Transforma datos raw del sistema fuente a formato del destino.
    """

    @abstractmethod
    def transform_record(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transforma un registro individual.

        Args:
            raw_data: Datos raw del sistema fuente

        Returns:
            Diccionario transformado listo para el destino
        """
        pass

    @abstractmethod
    def transform_related_records(
        self,
        raw_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Transforma registros relacionados (ej: líneas de un movimiento).

        Args:
            raw_data: Datos raw que contienen relaciones

        Returns:
            Lista de registros relacionados transformados
        """
        pass

    @abstractmethod
    def transform_batch(
        self,
        raw_batch: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Transforma un batch completo de registros principales y relacionados.

        Args:
            raw_batch: Lista de registros raw

        Returns:
            Tupla (registros_principales, registros_relacionados)
        """
        pass


class ValidationInterface(ABC):
    """Interface para validación de datos transformados."""

    @abstractmethod
    def validate(self, data: Dict[str, Any]) -> bool:
        """Valida que un registro cumpla reglas de negocio."""
        pass
