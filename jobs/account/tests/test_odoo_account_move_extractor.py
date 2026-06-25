"""OdooAccountMoveExtractor — id-fetch limit behavior."""

from unittest.mock import MagicMock

from account.services.extractors.odoo_account_move_extractor import (
    OdooAccountMoveExtractor,
)


def test_fetch_new_ids_passes_configured_limit_to_search() -> None:
    odoo = MagicMock()
    odoo.search.return_value = [1, 2, 3]
    extractor = OdooAccountMoveExtractor(odoo, extract_limit=2000)

    extractor.fetch_new_ids(last_processed_id=0)

    _, kwargs = odoo.search.call_args
    assert kwargs["limit"] == 2000


def test_fetch_new_ids_without_limit_passes_none() -> None:
    odoo = MagicMock()
    odoo.search.return_value = [1, 2, 3]
    extractor = OdooAccountMoveExtractor(odoo)

    extractor.fetch_new_ids(last_processed_id=0)

    _, kwargs = odoo.search.call_args
    assert kwargs["limit"] is None
