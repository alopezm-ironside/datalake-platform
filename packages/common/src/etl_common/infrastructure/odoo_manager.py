import logging
import xmlrpc.client
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple, Union

from etl_common.core.singleton_meta import SingletonMeta
from etl_common.utils.network import execute_with_retry

from .custom_https_transport import CustomHTTPSTransport

logger = logging.getLogger(__name__)


class OdooManager(metaclass=SingletonMeta):
    def __init__(self, url: str, db: str, user: str, password: str):
        self.url = url
        self.db = db
        self.user = user
        self.password = password
        self.common = None
        self.objects = None
        self.uid = None
        self._rpc_lock = Lock()

    def connect(self) -> int:
        logger.info("Conectando a Odoo...")
        transport = CustomHTTPSTransport(verify_ssl=False)
        self.common = xmlrpc.client.ServerProxy(
            f"{self.url}/xmlrpc/2/common", transport=transport
        )
        self.objects = xmlrpc.client.ServerProxy(
            f"{self.url}/xmlrpc/2/object", transport=transport
        )
        user_agent_env = {
            "base_location": self.url,
            "http_host": self.url.split("https://")[1]
            if "https://" in self.url
            else self.url,
            "remote_addr": "127.0.0.1",
        }
        self.uid = self.common.authenticate(
            self.db, self.user, self.password, user_agent_env
        )
        if not self.uid or self.uid <= 0:
            raise ConnectionError(f"Autenticacion fallida - uid={self.uid}")
        logger.info(f"Conectado a Odoo como UID: {self.uid}")
        return self.uid

    def _execute(
        self, model: str, method: str, args: list, kwargs: dict, operation_name: str
    ):
        """Wrapper thread-safe para lecturas. TODOS los metodos de lectura pasan por aqui."""
        with self._rpc_lock:
            return execute_with_retry(
                self.objects.execute_kw,
                self.db,
                self.uid,
                self.password,
                model,
                method,
                args,
                kwargs,
                operation_name=operation_name,
            )

    def search(
        self, model: str, domain: List, order: Optional[str] = None
    ) -> List[int]:
        kwargs = {}
        if order:
            kwargs["order"] = order
        return self._execute(
            model, "search", [domain], kwargs, f"Search {model} records"
        )

    def read(
        self, model: str, ids: List[int], fields: List[str]
    ) -> List[Dict[str, Any]]:
        return self._execute(
            model,
            "read",
            [ids],
            {"fields": fields},
            f"Read {model} ({len(ids)} records)",
        )

    def search_read(
        self,
        model: str,
        domain: List,
        fields: List[str],
        limit: Optional[int] = None,
        order: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        kwargs = {"fields": fields}
        if limit:
            kwargs["limit"] = limit
        if order:
            kwargs["order"] = order
        return self._execute(
            model, "search_read", [domain], kwargs, f"Search and read {model}"
        )

    def write(self, model: str, ids: List[int], values: Dict[str, Any]) -> bool:
        return self._execute(model, "write", [ids, values], {}, f"Write {model}")

    def create(
        self, model: str, values: Union[Dict[str, Any], List[Dict[str, Any]]]
    ) -> Any:
        """Dict -> 1 registro. List[Dict] -> N registros en 1 sola llamada RPC."""
        return self._execute(model, "create", [values], {}, f"Create {model}")

    def unlink(self, model: str, ids: List[int]) -> bool:
        return self._execute(model, "unlink", [ids], {}, f"Delete {model}")

    def write_many_parallel(
        self,
        model: str,
        writes: List[Tuple[int, Dict[str, Any]]],
        max_workers: int = 8,
    ) -> Tuple[int, int]:
        """
        Ejecuta multiples writes en paralelo, cada thread con su propia
        conexion XML-RPC para no bloquear el ServerProxy compartido.

        Args:
            model:       Modelo de Odoo (ej: 'product.pricelist.item')
            writes:      Lista de (item_id, values) a escribir
            max_workers: Threads en paralelo (recomendado 8 para Odoo SaaS)

        Returns:
            (success_count, failed_count)
        """
        if not writes:
            return 0, 0

        def _write_one(item_id: int, values: Dict[str, Any]) -> Tuple[int, bool]:
            # Conexion propia por thread — no comparte ServerProxy con nadie
            transport = CustomHTTPSTransport(verify_ssl=False)
            objects = xmlrpc.client.ServerProxy(
                f"{self.url}/xmlrpc/2/object",
                transport=transport,
            )
            try:
                objects.execute_kw(
                    self.db,
                    self.uid,
                    self.password,
                    model,
                    "write",
                    [[item_id], values],
                    {},
                )
                return item_id, True
            except Exception as e:
                logger.error(f"Error write {model} id={item_id}: {e}")
                return item_id, False

        success, failed = 0, 0
        total = len(writes)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(_write_one, item_id, values): item_id
                for item_id, values in writes
            }
            done = 0
            for future in as_completed(futures):
                _, ok = future.result()
                if ok:
                    success += 1
                else:
                    failed += 1
                done += 1
                if done % 100 == 0:
                    logger.info(f"  Progreso writes: {done}/{total}...")

        return success, failed
