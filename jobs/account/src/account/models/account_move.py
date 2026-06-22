
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import List, Optional

from etl_common.core.base import Base
from sqlalchemy import Date, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_bigquery.base import TimePartitioning


class AccountMove(Base):
    """
    Modelo para movimientos contables en BigQuery.
    """
    __tablename__ = 'odoo_raw.account_moves'
    
    # Configuración específica de BigQuery
    __table_args__ = {
        'bigquery_time_partitioning': TimePartitioning(
            field='date',
            type_='MONTH',
        ),
        'bigquery_clustering_fields': ['partner_name', 'move_type', 'state'],
        'bigquery_require_partition_filter': True,
        'bigquery_description': 'Raw accounting moves from Odoo ERP'
    }
    
    id: Mapped[int] = mapped_column(
        Integer, 
        primary_key=True, 
        autoincrement=False,
        nullable=False
    )
    name: Mapped[str] = mapped_column(String)
    move_type: Mapped[str] = mapped_column(String)
    date: Mapped[date] = mapped_column(Date)
    partner_id: Mapped[int] = mapped_column(Integer)
    partner_name: Mapped[str] = mapped_column(String)
    company_id: Mapped[int] = mapped_column(Integer)
    company_name: Mapped[str] = mapped_column(String)
    journal_id: Mapped[int] = mapped_column(Integer)
    journal_name: Mapped[str] = mapped_column(String)
    currency_name: Mapped[str] = mapped_column(String,)
    amount_untaxed: Mapped[float] = mapped_column(Float, default=0.0)
    amount_tax: Mapped[float] = mapped_column(Float, default=0.0)
    amount_total: Mapped[float] = mapped_column(Float, default=0.0)
    state: Mapped[str] = mapped_column(String)
    payment_state: Mapped[str] = mapped_column(String)
    ref: Mapped[str] = mapped_column(String)
    
    # Metadata
    synced_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
        nullable=False
    )
    sync_batch_id: Mapped[Optional[str]] = mapped_column(String)
    

    line_ids: Mapped[List["AccountMoveLine"]] = relationship( #noqa
        back_populates="account_move",
        cascade="all, delete-orphan",
        foreign_keys="AccountMoveLine.account_move_id"
    )
    
    def __repr__(self):
        return f"<AccountMove(id={self.id}, name={self.name}, total={self.amount_total})>"
    
    def to_dict(self):
        """Convierte el modelo a diccionario para insert masivo."""
        return {
            'id': self.id,
            'name': self.name,
            'move_type': self.move_type,
            'date': self.date,
            'partner_id': self.partner_id,
            'partner_name': self.partner_name,
            'company_id': self.company_id,
            'company_name': self.company_name,
            'journal_id': self.journal_id,
            'journal_name': self.journal_name,
            'currency_name': self.currency_name,
            'amount_untaxed': self.amount_untaxed,
            'amount_tax': self.amount_tax,
            'amount_total': self.amount_total,
            'state': self.state,
            'payment_state': self.payment_state,
            'ref': self.ref,
            'synced_at': self.synced_at,
            'sync_batch_id': self.sync_batch_id
        }