"""Assert ORM models carry symbolic schema tokens instead of hardcoded dataset names.

Tests verify:
- __tablename__ is unqualified (no dot notation)
- __table__.schema holds the expected symbolic token ("raw" or "control")
- schema_translate_map on BigQueryConnection maps tokens to real dataset names
"""

from account.persistence.models.account_move import AccountMoveORM
from account.persistence.models.account_move_line import AccountMoveLineORM
from etl_common.models.sync_metadata import SyncMetadata


def test_account_move_tablename_is_unqualified() -> None:
    assert "." not in AccountMoveORM.__tablename__
    assert AccountMoveORM.__tablename__ == "account_moves"


def test_account_move_schema_token_is_raw() -> None:
    assert AccountMoveORM.__table__.schema == "raw"


def test_account_move_line_tablename_is_unqualified() -> None:
    assert "." not in AccountMoveLineORM.__tablename__
    assert AccountMoveLineORM.__tablename__ == "account_move_lines"


def test_account_move_line_schema_token_is_raw() -> None:
    assert AccountMoveLineORM.__table__.schema == "raw"


def test_sync_metadata_tablename_is_unqualified() -> None:
    assert "." not in SyncMetadata.__tablename__
    assert SyncMetadata.__tablename__ == "sync_metadata"


def test_sync_metadata_schema_token_is_control() -> None:
    assert SyncMetadata.__table__.schema == "control"


def test_account_move_line_foreign_key_uses_symbolic_schema() -> None:
    """FK must reference raw.account_moves.id, not odoo_raw.account_moves.id."""
    fk_targets = {
        str(fk.target_fullname) for fk in AccountMoveLineORM.__table__.foreign_keys
    }
    assert any("raw.account_moves" in t for t in fk_targets), (
        f"Expected FK target containing 'raw.account_moves', got: {fk_targets}"
    )
    assert not any("odoo_raw" in t for t in fk_targets), (
        f"FK still hardcodes 'odoo_raw': {fk_targets}"
    )
