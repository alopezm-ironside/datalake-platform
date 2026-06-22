"""Entry point for the account ETL Cloud Run Job.

Exposed as the `account-job` console script (see pyproject.toml) and invoked
directly by the container ENTRYPOINT.
"""
import logging

from etl_common.conf.settings import Settings
from etl_common.infrastructure.odoo_manager import OdooManager

from account.apps.account_move_app import AccountMoveApp

logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    settings = Settings()

    # Instantiate the Odoo singleton with credentials so that downstream
    # no-arg OdooManager() calls resolve to this configured instance.
    OdooManager(
        url=settings.ODOO_URL,
        db=settings.ODOO_DB,
        user=settings.ODOO_USER,
        password=settings.ODOO_PASSWORD,
    )

    AccountMoveApp(settings).run()


if __name__ == "__main__":
    main()
