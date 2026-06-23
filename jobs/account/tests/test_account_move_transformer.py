"""Tests for the refactored AccountMoveTransformer (Phase 6 — Change 2)."""

from unittest.mock import MagicMock


def _make_tax_cache(rate: float = 19.0) -> MagicMock:
    cache = MagicMock()
    cache.get_tax_rate.return_value = rate
    return cache


def _raw_move(move_id: int = 1) -> dict:
    return {
        "id": move_id,
        "name": f"INV/2024/{move_id:04d}",
        "move_type": "out_invoice",
        "date": "2024-01-15",
        "partner_id": [7, "Acme Corp"],
        "company_id": [1, "My Co"],
        "journal_id": [3, "Customer Invoices"],
        "currency_id": [5, "CLP"],
        "amount_untaxed": 100.0,
        "amount_tax": 19.0,
        "amount_total": 119.0,
        "state": "posted",
        "payment_state": "not_paid",
        "ref": "",
        "_lines": [
            {
                "id": move_id * 10,
                "product_id": [5, "Widget"],
                "name": "Widget sale",
                "quantity": 1.0,
                "price_unit": 100.0,
                "discount": 0.0,
                "price_subtotal": 100.0,
                "price_total": 119.0,
                "account_id": [42, "Sales Account"],
                "debit": 119.0,
                "credit": 0.0,
                "tax_ids": [1],
            }
        ],
    }


def test_transform_maps_raw_dict_to_account_move_entity():
    """transform() returns AccountMove entities (not dicts)."""
    from account.domain.account_move import AccountMove
    from account.services.transformers.account_move_transformer import (
        AccountMoveTransformer,
    )

    transformer = AccountMoveTransformer(tax_cache=_make_tax_cache())
    result = transformer.transform([_raw_move(1)])

    assert len(result) == 1
    assert isinstance(result[0], AccountMove)


def test_transform_populates_lines():
    """Transformer populates lines on the AccountMove aggregate."""
    from account.domain.account_move_line import AccountMoveLine
    from account.services.transformers.account_move_transformer import (
        AccountMoveTransformer,
    )

    transformer = AccountMoveTransformer(tax_cache=_make_tax_cache())
    result = transformer.transform([_raw_move(1)])

    move = result[0]
    assert len(move.lines) == 1
    assert isinstance(move.lines[0], AccountMoveLine)


def test_transform_tax_amount_is_price_total_minus_price_subtotal():
    """tax_amount on each line = price_total - price_subtotal."""
    from account.services.transformers.account_move_transformer import (
        AccountMoveTransformer,
    )

    transformer = AccountMoveTransformer(tax_cache=_make_tax_cache(19.0))
    result = transformer.transform([_raw_move(1)])

    line = result[0].lines[0]
    assert line.tax_amount == line.price_total - line.price_subtotal


def test_transform_partner_company_journal_tuple_flattening():
    """partner_id, company_id, and journal_id tuples are flattened correctly."""
    from account.services.transformers.account_move_transformer import (
        AccountMoveTransformer,
    )

    transformer = AccountMoveTransformer(tax_cache=_make_tax_cache())
    result = transformer.transform([_raw_move(1)])

    move = result[0]
    assert move.partner_id == 7
    assert move.partner_name == "Acme Corp"
    assert move.company_id == 1
    assert move.company_name == "My Co"
    assert move.journal_id == 3
    assert move.journal_name == "Customer Invoices"
    assert move.currency_name == "CLP"


def test_transform_drops_records_without_id():
    """Records with no id are silently dropped by the private validation."""
    from account.services.transformers.account_move_transformer import (
        AccountMoveTransformer,
    )

    raw = _raw_move(1)
    raw.pop("id")

    transformer = AccountMoveTransformer(tax_cache=_make_tax_cache())
    result = transformer.transform([raw])

    assert result == []


def test_transform_drops_records_without_date():
    """Records with no date are silently dropped by the private validation."""
    from account.services.transformers.account_move_transformer import (
        AccountMoveTransformer,
    )

    raw = _raw_move(1)
    raw.pop("date")

    transformer = AccountMoveTransformer(tax_cache=_make_tax_cache())
    result = transformer.transform([raw])

    assert result == []


def test_transform_returns_all_valid_from_mixed_batch():
    """Only invalid records are dropped; valid ones pass through."""
    from account.services.transformers.account_move_transformer import (
        AccountMoveTransformer,
    )

    valid = _raw_move(1)
    invalid_no_id = _raw_move(2)
    invalid_no_id.pop("id")

    transformer = AccountMoveTransformer(tax_cache=_make_tax_cache())
    result = transformer.transform([valid, invalid_no_id])

    assert len(result) == 1
    assert result[0].id == 1


def test_transform_returns_list_type_annotation():
    """transform() result is a list (not a generator or tuple)."""
    from account.services.transformers.account_move_transformer import (
        AccountMoveTransformer,
    )

    transformer = AccountMoveTransformer(tax_cache=_make_tax_cache())
    result = transformer.transform([_raw_move(1)])

    assert isinstance(result, list)


def test_transformer_accepts_tax_cache_only_no_sync_batch_id():
    """Constructor takes only tax_cache; sync_batch_id is stamped by the repository."""
    from account.services.transformers.account_move_transformer import (
        AccountMoveTransformer,
    )

    transformer = AccountMoveTransformer(tax_cache=_make_tax_cache())
    assert transformer is not None
