import logging

from sqlalchemy import create_engine

from ..core.base import Base
from ..core.singleton_meta import SingletonMeta

_logger = logging.getLogger(__name__)

class PostgresDBConnection(metaclass=SingletonMeta):
    """
    Singleton class to manage the connection to the Postgres database.
    """
    def __init__(self, host, port, database, user, password):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.engine = create_engine(f'postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}')
        self.connection = self.engine.connect()

    def create_tables(self):
        """Crea las tablas definidas en los modelos si no existen."""
        _logger.info("🛠️  Verificando/Creando tablas en la base de datos...")
        try:
            Base.metadata.create_all(self.engine)
        except Exception as e:
            _logger.error(f"❌ Error al crear tablas en Postgres: {e}")
            raise
        _logger.info("✅  Tablas verificadas.")
