import xmlrpc.client
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from typing import Any

from etl_common.core.singleton_meta import SingletonMeta
from etl_common.observability import get_logger
from etl_common.utils.network import execute_with_retry

from .custom_https_transport import CustomHTTPSTransport

_log = get_logger(__name__)


class OdooManager(metaclass=SingletonMeta):
    def __init__(self, url: str, db: str, user: str, password: str) -> None:
        self.url = url
        self.db = db
        self.user = user
        self.password = password
        self.common: xmlrpc.client.ServerProxy | None = None
        self.objects: xmlrpc.client.ServerProxy | None = None
        self.uid: int | None = None
        self._rpc_lock = Lock()

    def connect(self) -> int:
        _log.info("odoo_connecting")
        transport = CustomHTTPSTransport(verify_ssl=False)
        self.common = xmlrpc.client.ServerProxy(
            f"{self.url}/xmlrpc/2/common", transport=transport
        )
        self.objects = xmlrpc.client.ServerProxy(
            f"{self.url}/xmlrpc/2/object", transport=transport
        )
        user_agent_env: dict[str, str] = {
            "base_location": self.url,
            "http_host": self.url.split("https://")[1]
            if "https://" in self.url
            else self.url,
            "remote_addr": "127.0.0.1",
        }
        uid: Any = self.common.authenticate(
            self.db, self.user, self.password, user_agent_env
        )
        if not uid or uid <= 0:
            raise ConnectionError(f"Autenticacion fallida - uid={uid}")
        self.uid = int(uid)
        _log.info("odoo_connected", uid=self.uid)
        return self.uid

    def _execute(
        self,
        model: str,
        method: str,
        args: list[Any],
        kwargs: dict[str, Any],
        operation_name: str,
    ) -> Any:
        # Thread-safe wrapper: all RPC calls serialize through the shared lock.
        with self._rpc_lock:
            assert self.objects is not None, (
                "OdooManager.connect() must be called first"
            )
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
        self,
        model: str,
        domain: list[Any],
        order: str | None = None,
        limit: int | None = None,
    ) -> list[int]:
        kwargs: dict[str, Any] = {}
        if order:
            kwargs["order"] = order
        if limit:
            kwargs["limit"] = limit
        result: list[int] = self._execute(
            model, "search", [domain], kwargs, f"Search {model} records"
        )
        return result

    def read(
        self, model: str, ids: list[int], fields: list[str]
    ) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = self._execute(
            model,
            "read",
            [ids],
            {"fields": fields},
            f"Read {model} ({len(ids)} records)",
        )
        return result

    def search_read(
        self,
        model: str,
        domain: list[Any],
        fields: list[str],
        limit: int | None = None,
        order: str | None = None,
    ) -> list[dict[str, Any]]:
        kwargs: dict[str, Any] = {"fields": fields}
        if limit:
            kwargs["limit"] = limit
        if order:
            kwargs["order"] = order
        result: list[dict[str, Any]] = self._execute(
            model, "search_read", [domain], kwargs, f"Search and read {model}"
        )
        return result

    def write(self, model: str, ids: list[int], values: dict[str, Any]) -> bool:
        result: bool = self._execute(
            model, "write", [ids, values], {}, f"Write {model}"
        )
        return result

    def create(self, model: str, values: dict[str, Any] | list[dict[str, Any]]) -> Any:
        """Single dict creates one record; list of dicts creates N in one RPC call."""
        return self._execute(model, "create", [values], {}, f"Create {model}")

    def unlink(self, model: str, ids: list[int]) -> bool:
        result: bool = self._execute(model, "unlink", [ids], {}, f"Delete {model}")
        return result

    def write_many_parallel(
        self,
        model: str,
        writes: list[tuple[int, dict[str, Any]]],
        max_workers: int = 8,
    ) -> tuple[int, int]:
        """Execute multiple writes in parallel via per-thread XML-RPC connections.

        Returns (success_count, failed_count).
        """
        if not writes:
            return 0, 0

        def _write_one(item_id: int, values: dict[str, Any]) -> tuple[int, bool]:
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
                _log.error("write_failed", model=model, item_id=item_id, error=str(e))
                return item_id, False

        success, failed = 0, 0
        total = len(writes)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(_write_one, item_id, values): item_id
                for item_id, values in writes
            }
            for done, future in enumerate(as_completed(futures), start=1):
                _, ok = future.result()
                if ok:
                    success += 1
                else:
                    failed += 1
                if done % 100 == 0:
                    _log.info("write_progress", done=done, total=total)

        return success, failed
