from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from etl_common.core.base import Base
from sqlalchemy import ARRAY, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_bigquery.base import TimePartitioning


class AccountMoveLine(Base):
    """Modelo para líneas de movimientos contables en BigQuery."""
    __tablename__ = 'odoo_raw.account_move_lines'

    # Configuración específica de BigQuery
    __table_args__ = {
        'bigquery_time_partitioning': TimePartitioning(
            field='date', 
            type_="MONTH"
        ),
        'bigquery_require_partition_filter': True,
        'bigquery_clustering_fields': ['account_move_id', 'account_id', 'product_id'],
        'bigquery_description': 'Accounting move lines from Odoo ERP'
    }

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=False,
        nullable=False
    )

    product_id: Mapped[int] = mapped_column(default=0)
    description: Mapped[str] = mapped_column(default='')
    date: Mapped[date] = mapped_column(Date, nullable=False)
    quantity: Mapped[int] = mapped_column(default=0)
    price_unit: Mapped[float] = mapped_column(default=0.0)
    discount: Mapped[float] = mapped_column(default=0.0)
    price_subtotal: Mapped[float] = mapped_column(default=0.0)
    price_total: Mapped[float] = mapped_column(default=0.0)
    account_id: Mapped[int] = mapped_column(default=0)
    account_name: Mapped[str] = mapped_column(default='')
    debit: Mapped[float] = mapped_column(default=0.0)
    credit: Mapped[float] = mapped_column(default=0.0)
    tax_ids: Mapped[List[int]] = mapped_column(ARRAY(Integer), default=[], nullable=True)
    tax_rate: Mapped[float] = mapped_column(default=0.0)
    tax_amount: Mapped[float] = mapped_column(default=0.0)

    # Metadata
    synced_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
        nullable=False
    )
    sync_batch_id: Mapped[Optional[str]] = mapped_column(String)

    account_move_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("odoo_raw.account_moves.id", name="fk_account_move"),
        nullable=False
    )

    # Relación inversa
    account_move: Mapped["AccountMove"] = relationship(  # noqa
        back_populates="line_ids",
        foreign_keys=[account_move_id]
    )

    def __repr__(self):
        return f"<AccountMoveLine(id={self.id}, move_id={self.account_move_id}, total={self.price_total})>"

    def to_dict(self):
        """Convierte el modelo a diccionario para insert masivo."""
        return {
            'id': self.id,
            'account_move_id': self.account_move_id,
            'description': self.description,
            'date': self.date,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'price_unit': self.price_unit,
            'discount': self.discount,
            'price_subtotal': self.price_subtotal,
            'price_total': self.price_total,
            'account_id': self.account_id,
            'account_name': self.account_name,
            'debit': self.debit,
            'credit': self.credit,
            'tax_ids': self.tax_ids or [],
            'tax_rate': self.tax_rate,
            'tax_amount': self.tax_amount,
            'synced_at': self.synced_at,
            'sync_batch_id': self.sync_batch_id
        }
