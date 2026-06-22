import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from etl_common.interfaces.extractor_interface import TaxCacheInterface
from etl_common.interfaces.transformer_interface import TransformerInterface, ValidationInterface

_logger = logging.getLogger(__name__)


class AccountMoveTransformer(TransformerInterface, ValidationInterface):
    """
    Implementación de TransformerInterface para movimientos contables.
    """
    
    def __init__(self, tax_cache: TaxCacheInterface, sync_batch_id: str):
        self.tax_cache = tax_cache
        self.sync_batch_id = sync_batch_id
    
    def transform_record(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transforma un movimiento contable.
        """

        # Extraer datos de relaciones
        partner_data = raw_data.get('partner_id') or []
        company_data = raw_data.get('company_id') or []
        journal_data = raw_data.get('journal_id') or []
        currency_data = raw_data.get('currency_id') or []
        
        return {
            'id': raw_data.get('id'),
            'name': raw_data.get('name', ''),
            'move_type': raw_data.get('move_type', ''),
            'date': raw_data.get('date'),            
            'partner_id': partner_data[0] if len(partner_data) > 0 else None,
            'partner_name': partner_data[1] if len(partner_data) > 1 else '',
            'company_id': company_data[0] if len(company_data) > 0 else None,
            'company_name': company_data[1] if len(company_data) > 1 else 'N/A',
            'journal_id': journal_data[0] if len(journal_data) > 0 else None,
            'journal_name': journal_data[1] if len(journal_data) > 1 else 'N/A',
            'currency_name': currency_data[1] if len(currency_data) > 1 else 'CLP',
            'amount_untaxed': float(raw_data.get('amount_untaxed', 0)),
            'amount_tax': float(raw_data.get('amount_tax', 0)),
            'amount_total': float(raw_data.get('amount_total', 0)),
            'state': raw_data.get('state', ''),
            'payment_state': raw_data.get('payment_state', ''),
            'ref': raw_data.get('ref', ''),
            
            # Metadata
            'synced_at': datetime.now(timezone.utc),
            'sync_batch_id': self.sync_batch_id
        }
    
    def transform_related_records(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Transforma líneas de un movimiento contable."""
        move_id = raw_data.get('id')
        lines_raw = raw_data.get('_lines', [])
        move_date = raw_data.get('date')

        transformed_lines = []
        for line_raw in lines_raw:
            line_transformed = self._transform_line(line_raw, move_id, move_date)
            transformed_lines.append(line_transformed)
        
        return transformed_lines
    
    def transform_batch(
        self, 
        raw_batch: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Transforma un batch completo de movimientos y líneas."""
        transformed_moves = []
        transformed_lines = []
        
        for raw_move in raw_batch:
            # Validar antes de transformar
            if not self.validate(raw_move):
                _logger.warning(f"⚠️ Movimiento {raw_move.get('id')} no pasó validación, se omite")
                continue
            
            # Transformar movimiento
            move_transformed = self.transform_record(raw_move)
            transformed_moves.append(move_transformed)
            
            # Transformar líneas
            lines_transformed = self.transform_related_records(raw_move)
            transformed_lines.extend(lines_transformed)
        
        return transformed_moves, transformed_lines
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """Valida reglas de negocio básicas."""

        if not data.get('id'):
            _logger.warning("⚠️ Movimiento sin ID")
            return False
        
        if not data.get('date'):
            _logger.warning(f"⚠️ Movimiento {data.get('id')} sin fecha")
            return False
        
        return True
    
    def _transform_line(self, line_raw: Dict[str, Any], move_id: int, move_date: str) -> Dict[str, Any]:
        """Transforma una línea individual."""
        product_data = line_raw.get('product_id') or []
        account_data = line_raw.get('account_id') or []
        
        # Calcular tax_amount
        price_subtotal = float(line_raw.get('price_subtotal', 0))
        price_total = float(line_raw.get('price_total', 0))
        tax_amount = price_total - price_subtotal if price_subtotal else 0
        
        # Obtener tax_rate
        tax_ids = line_raw.get('tax_ids', [])
        tax_rate = self.tax_cache.get_tax_rate(tax_ids) if tax_ids else 0.0
        
        return {
            'id': line_raw.get('id'),
            'account_move_id': move_id,
            'product_id': product_data[0] if len(product_data) > 0 else None,
            'description': line_raw.get('name', ''),
            'quantity': float(line_raw.get('quantity', 0)),
            'date': move_date,
            'price_unit': float(line_raw.get('price_unit', 0)),
            'discount': float(line_raw.get('discount', 0)),
            'price_subtotal': price_subtotal,
            'price_total': price_total,
            'account_id': account_data[0] if len(account_data) > 0 else None,
            'account_name': account_data[1] if len(account_data) > 1 else '',
            'debit': float(line_raw.get('debit', 0)),
            'credit': float(line_raw.get('credit', 0)),
            'tax_ids': tax_ids,
            'tax_rate': tax_rate,
            'tax_amount': tax_amount,
            
            # Metadata
            'synced_at': datetime.now(timezone.utc),
            'sync_batch_id': self.sync_batch_id
        }
