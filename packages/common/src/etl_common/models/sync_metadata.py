from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_bigquery.base import TimePartitioning

from etl_common.core.base import Base


class SyncMetadata(Base):
    """Modelo para tracking de sincronizaciones."""
    __tablename__ = 'control.sync_metadata'

    # Configuración específica de BigQuery
    __table_args__ = {
        'bigquery_time_partitioning': TimePartitioning(
            field='started_at',
            type_='YEAR',
        ),
        'bigquery_clustering_fields': ['module_name', 'status'],
        'bigquery_description': 'Sync execution metadata and tracking'
    }

    # Primary Key
    sync_id: Mapped[str] = mapped_column(
        String, primary_key=True, nullable=False)

    # Sync identification
    module_name: Mapped[str] = mapped_column(String, nullable=False)
    sync_type: Mapped[Optional[str]] = mapped_column(
        String)  # 'full', 'incremental'

    # Execution details
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(
        String, nullable=False)  # 'running', 'success', 'failed'

    # Data tracking
    last_processed_id: Mapped[Optional[int]] = mapped_column(Integer)
    records_processed: Mapped[Optional[int]
                              ] = mapped_column(Integer, default=0)
    records_inserted: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    records_failed: Mapped[Optional[int]] = mapped_column(Integer, default=0)

    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    # Performance
    execution_time_seconds: Mapped[Optional[float]] = mapped_column(Float)
    odoo_api_calls: Mapped[Optional[int]] = mapped_column(Integer, default=0)

    def __repr__(self):
        return f"<SyncMetadata(id={self.sync_id}, module={self.module_name}, status={self.status})>"
