from abc import ABC, abstractmethod


class SyncAppInterface(ABC):
    """Interface base para aplicaciones de sincronización de módulos."""

    @abstractmethod
    def run(self):
        """Ejecuta el proceso de sincronización."""
        pass

    @abstractmethod
    def get_module_name(self) -> str:
        """Retorna el nombre del módulo."""
        pass
