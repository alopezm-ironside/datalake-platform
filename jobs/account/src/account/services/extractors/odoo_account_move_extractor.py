import logging
from typing import Any, Dict, List

from etl_common.infrastructure.odoo_manager import OdooManager
from etl_common.interfaces.extractor_interface import ExtractorInterface, TaxCacheInterface

_logger = logging.getLogger(__name__)


class OdooAccountMoveExtractor(ExtractorInterface, TaxCacheInterface):
    """
    Implementación de ExtractorInterface para Odoo.
    """
    
    MOVE_FIELDS = [
        'id', 'name', 'move_type', 'date',
        'partner_id', 'ref', 'journal_id', 'state',
        'payment_state', 'company_id', 'currency_id', 'amount_untaxed',
        'amount_tax', 'amount_total', 'line_ids', 'write_date'
    ]
    
    LINE_FIELDS = [
        'id', 'move_id', 'product_id', 'name', 'quantity', 'price_unit',
        'discount', 'price_subtotal', 'price_total', 'tax_ids',
        'account_id', 'debit', 'credit'
    ]
    
    def __init__(self, odoo_manager: OdooManager):
        self.odoo = odoo_manager
        self.tax_cache = {}
    
    def get_source_name(self) -> str:
        return "odoo"
    
    def fetch_new_ids(self, last_processed_id: int = 0) -> List[int]:
        """Implementación específica para Odoo."""
        _logger.info(f"🔍 [{self.get_source_name()}] Buscando movimientos desde ID: {last_processed_id}")
        
        domain = [
            ('id', '>', last_processed_id),
            ('line_ids', '!=', False)
        ]
        
        move_ids = self.odoo.search(
            'account.move',
            domain,
            order='id asc'
        )
        
        _logger.info(f"✅ [{self.get_source_name()}] Encontrados {len(move_ids)} movimientos nuevos")
        return move_ids
    
    def fetch_batch(self, ids: List[int]) -> List[Dict[str, Any]]:
        """Implementación específica para Odoo."""
        if not ids:
            return []
        
        _logger.info(f"📥 [{self.get_source_name()}] Extrayendo {len(ids)} movimientos...")
        
        # Fetch movimientos
        moves = self.odoo.read('account.move', ids, self.MOVE_FIELDS)
        
        # Recolectar todos los IDs de líneas
        all_line_ids = []
        for move in moves:
            all_line_ids.extend(move.get('line_ids', []))
        
        # Fetch todas las líneas en batch
        lines_data = []
        if all_line_ids:
            _logger.info(f"📥 [{self.get_source_name()}] Extrayendo {len(all_line_ids)} líneas...")
            lines_data = self.odoo.read('account.move.line', all_line_ids, self.LINE_FIELDS)
            
            # Pre-cargar impuestos
            self._prefetch_taxes(lines_data)
        
        # Mapear líneas por move_id
        lines_by_move = {}
        for line in lines_data:
            move_id = line.get('move_id')[0] if line.get('move_id') else None
            if move_id:
                if move_id not in lines_by_move:
                    lines_by_move[move_id] = []
                lines_by_move[move_id].append(line)
        
        # Adjuntar líneas a movimientos
        for move in moves:
            move['_lines'] = lines_by_move.get(move['id'], [])
        
        _logger.info(f"✅ [{self.get_source_name()}] Extraídos {len(moves)} movimientos con líneas")
        return moves
    
    def _prefetch_taxes(self, lines: List[Dict[str, Any]]):
        """Pre-carga impuestos en caché (método auxiliar específico de Odoo)."""
        all_tax_ids = set()
        for line in lines:
            tax_ids = line.get('tax_ids', [])
            all_tax_ids.update(tax_ids)
        
        missing_tax_ids = [tid for tid in all_tax_ids if tid not in self.tax_cache]
        
        if not missing_tax_ids:
            return
        
        _logger.info(f"📥 [{self.get_source_name()}] Pre-cargando {len(missing_tax_ids)} impuestos...")
        
        try:
            taxes = self.odoo.read('account.tax', missing_tax_ids, ['id', 'amount'])
            for tax in taxes:
                self.tax_cache[tax['id']] = tax
            _logger.info(f"✅ [{self.get_source_name()}] Impuestos cargados en caché")
        except Exception as e:
            _logger.warning(f"⚠️ [{self.get_source_name()}] Error cargando impuestos: {e}")
    
    def get_tax_rate(self, tax_ids: List[int]) -> float:
        """Implementación de TaxCacheInterface."""
        if not tax_ids:
            return 0.0
        
        tax_data = self.tax_cache.get(tax_ids[0], {})
        return tax_data.get('amount', 0.0)