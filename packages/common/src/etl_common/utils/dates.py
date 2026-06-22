import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def convert_utc_to_chile(date_string: str) -> str:
    """Convierte fechas UTC a zona horaria de Chile (UTC-3)."""
    if not date_string:
        return ''

    try:
        date_str = str(date_string)

        # Si ya tiene formato YYYY-MM-DD, devolverlo tal cual
        if len(date_str) == 10 and date_str[4] == '-' and date_str[7] == '-':
            return date_str

        # Asumimos formato con hora y ajustamos zona horaria
        dt = datetime.strptime(date_str[:19], '%Y-%m-%d %H:%M:%S')
        dt_chile = dt - timedelta(hours=3)

        return dt_chile.strftime('%Y-%m-%d')
    except Exception as e:
        logger.warning(f"⚠️ Error al convertir fecha '{date_string}': {e}")
        return date_string[:10] if date_string else ''
