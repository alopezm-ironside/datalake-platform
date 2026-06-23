import logging
from typing import Any, ClassVar

from etl_common.infrastructure.odoo_manager import OdooManager
from etl_common.interfaces.extractor_interface import ExtractorInterface
from etl_common.interfaces.tax_cache_interface import TaxCacheInterface

_logger = logging.getLogger(__name__)


class OdooAccountMoveExtractor(ExtractorInterface, TaxCacheInterface):
    """Extrae account.move y sus líneas desde Odoo vía XML-RPC."""

    MOVE_FIELDS: ClassVar[list[str]] = [
        "id",
        "name",
        "move_type",
        "date",
        "partner_id",
        "ref",
        "journal_id",
        "state",
        "payment_state",
        "company_id",
        "currency_id",
        "amount_untaxed",
        "amount_tax",
        "amount_total",
        "line_ids",
        "write_date",
    ]

    LINE_FIELDS: ClassVar[list[str]] = [
        "id",
        "move_id",
        "product_id",
        "name",
        "quantity",
        "price_unit",
        "discount",
        "price_subtotal",
        "price_total",
        "tax_ids",
        "account_id",
        "debit",
        "credit",
    ]

    def __init__(self, odoo_manager: OdooManager) -> None:
        self.odoo = odoo_manager
        self.tax_cache: dict[int, dict[str, Any]] = {}

    def get_source_name(self) -> str:
        return "odoo"

    def fetch_new_ids(self, last_processed_id: int = 0) -> list[int]:
        _logger.info(f"🔍 Buscando movimientos desde ID: {last_processed_id}")
        domain = [("id", ">", last_processed_id), ("line_ids", "!=", False)]
        move_ids = self.odoo.search("account.move", domain, order="id asc")
        _logger.info(f"✅ Encontrados {len(move_ids)} movimientos nuevos")
        return move_ids

    def fetch_batch(self, ids: list[int]) -> list[dict[str, Any]]:
        if not ids:
            return []

        _logger.info(f"📥 Extrayendo {len(ids)} movimientos...")
        moves = self.odoo.read("account.move", ids, self.MOVE_FIELDS)

        all_line_ids: list[int] = []
        for move in moves:
            all_line_ids.extend(move.get("line_ids", []))

        lines_data: list[dict[str, Any]] = []
        if all_line_ids:
            _logger.info(f"📥 Extrayendo {len(all_line_ids)} líneas...")
            lines_data = self.odoo.read(
                "account.move.line", all_line_ids, self.LINE_FIELDS
            )
            self._prefetch_taxes(lines_data)

        lines_by_move: dict[int, list[dict[str, Any]]] = {}
        for line in lines_data:
            move_ref = line.get("move_id")
            move_id = move_ref[0] if move_ref else None
            if move_id:
                lines_by_move.setdefault(move_id, []).append(line)

        for move in moves:
            move["_lines"] = lines_by_move.get(move["id"], [])

        _logger.info(f"✅ Extraídos {len(moves)} movimientos con líneas")
        return moves

    def _prefetch_taxes(self, lines: list[dict[str, Any]]) -> None:
        all_tax_ids: set[int] = set()
        for line in lines:
            all_tax_ids.update(line.get("tax_ids", []))

        missing_tax_ids = [tid for tid in all_tax_ids if tid not in self.tax_cache]
        if not missing_tax_ids:
            return

        _logger.info(f"📥 Pre-cargando {len(missing_tax_ids)} impuestos...")
        try:
            taxes = self.odoo.read("account.tax", missing_tax_ids, ["id", "amount"])
            for tax in taxes:
                self.tax_cache[tax["id"]] = tax
        except Exception as e:
            _logger.warning(f"⚠️ Error cargando impuestos: {e}")

    def get_tax_rate(self, tax_ids: list[int]) -> float:
        if not tax_ids:
            return 0.0
        tax_data = self.tax_cache.get(tax_ids[0], {})
        return float(tax_data.get("amount", 0.0))
