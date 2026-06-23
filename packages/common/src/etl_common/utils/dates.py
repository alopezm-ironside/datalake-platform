from datetime import datetime
from zoneinfo import ZoneInfo

from etl_common.observability import get_logger

_log = get_logger(__name__)

_UTC = ZoneInfo("UTC")
_CHILE = ZoneInfo("America/Santiago")


def convert_utc_to_chile(date_string: str) -> str:
    """Convierte fechas UTC a zona horaria de Chile."""
    if not date_string:
        return ""

    try:
        date_str = str(date_string)

        if len(date_str) == 10 and date_str[4] == "-" and date_str[7] == "-":
            return date_str

        dt = datetime.strptime(date_str[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=_UTC)
        return dt.astimezone(_CHILE).strftime("%Y-%m-%d")
    except Exception as e:
        _log.warning(
            "date_conversion_failed",
            date_string=date_string,
            error=type(e).__name__,
        )
        return date_string[:10] if date_string else ""
