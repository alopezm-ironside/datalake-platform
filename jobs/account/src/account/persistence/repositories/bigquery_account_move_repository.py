"""BigQuery append-only repository for AccountMove aggregates."""

from datetime import datetime, timezone

from etl_common.infrastructure.bigquery_connection import BigQueryConnection
from etl_common.interfaces.repository_interface import RepositoryInterface
from sqlalchemy.orm import Session

from account.domain.account_move import AccountMove
from account.persistence.models.account_move import AccountMoveORM
from account.persistence.models.account_move_line import AccountMoveLineORM


class BigQueryAccountMoveRepository(RepositoryInterface[AccountMove]):
    """Appends AccountMove aggregates (header + lines) to BigQuery Bronze.

    Owns its SQLAlchemy Session; commits data in save_batch and rolls back
    on any failure before re-raising so the pipeline can record the error.
    """

    def __init__(self, connection: BigQueryConnection, sync_batch_id: str) -> None:
        self._engine = connection.engine
        self._sync_batch_id = sync_batch_id

    def save_batch(self, entities: list[AccountMove]) -> int:
        """Append all AccountMove aggregates and their lines in one transaction."""
        synced_at = datetime.now(timezone.utc)
        orm_rows: list[AccountMoveORM | AccountMoveLineORM] = []
        for entity in entities:
            orm_rows.extend(self._to_orm(entity, synced_at))

        with Session(self._engine) as session:
            try:
                session.add_all(orm_rows)
                session.commit()
            except Exception:
                session.rollback()
                raise

        return len(entities)

    def _to_orm(
        self, entity: AccountMove, synced_at: datetime
    ) -> list[AccountMoveORM | AccountMoveLineORM]:
        """Map one AccountMove entity (+ lines) to ORM rows, stamping metadata."""
        move_orm = AccountMoveORM(
            id=entity.id,
            name=entity.name,
            move_type=entity.move_type,
            date=entity.date,
            partner_id=entity.partner_id,
            partner_name=entity.partner_name,
            company_id=entity.company_id,
            company_name=entity.company_name,
            journal_id=entity.journal_id,
            journal_name=entity.journal_name,
            currency_name=entity.currency_name,
            amount_untaxed=entity.amount_untaxed,
            amount_tax=entity.amount_tax,
            amount_total=entity.amount_total,
            state=entity.state,
            payment_state=entity.payment_state,
            ref=entity.ref,
            synced_at=synced_at,
            sync_batch_id=self._sync_batch_id,
        )
        rows: list[AccountMoveORM | AccountMoveLineORM] = [move_orm]
        for line in entity.lines:
            rows.append(
                AccountMoveLineORM(
                    id=line.id,
                    account_move_id=entity.id,
                    product_id=line.product_id,
                    description=line.description,
                    date=line.date,
                    quantity=line.quantity,
                    price_unit=line.price_unit,
                    discount=line.discount,
                    price_subtotal=line.price_subtotal,
                    price_total=line.price_total,
                    account_id=line.account_id,
                    account_name=line.account_name,
                    debit=line.debit,
                    credit=line.credit,
                    tax_ids=line.tax_ids,
                    tax_rate=line.tax_rate,
                    tax_amount=line.tax_amount,
                    synced_at=synced_at,
                    sync_batch_id=self._sync_batch_id,
                )
            )
        return rows
