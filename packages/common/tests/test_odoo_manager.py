"""OdooManager.search — query kwargs construction."""

from unittest.mock import MagicMock

from etl_common.infrastructure.odoo_manager import OdooManager


def _manager_with_mock_rpc() -> OdooManager:
    manager = OdooManager(url="http://odoo", db="db", user="u", password="p")
    manager.objects = MagicMock()
    manager.uid = 1
    return manager


def _search_kwargs(manager: OdooManager) -> dict[str, object]:
    return manager.objects.execute_kw.call_args.args[6]  # type: ignore[union-attr]


def test_search_includes_limit_when_provided() -> None:
    manager = _manager_with_mock_rpc()
    manager.objects.execute_kw.return_value = [1, 2]  # type: ignore[union-attr]

    manager.search("account.move", [["id", ">", 0]], order="id asc", limit=2000)

    kwargs = _search_kwargs(manager)
    assert kwargs["limit"] == 2000
    assert kwargs["order"] == "id asc"


def test_search_omits_limit_when_not_provided() -> None:
    manager = _manager_with_mock_rpc()
    manager.objects.execute_kw.return_value = [1, 2]  # type: ignore[union-attr]

    manager.search("account.move", [["id", ">", 0]])

    assert "limit" not in _search_kwargs(manager)
