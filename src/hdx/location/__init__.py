from datetime import datetime

from ._version import version as __version__  # noqa: F401
from hdx.utilities.dateparse import get_timestamp_from_datetime


def get_int_timestamp(date: datetime) -> int:
    """
    Get integer timestamp from datetime object

    Args:
        date (datetime): datetime object

    Returns:
        int: Integer timestamp
    """
    return int(round(get_timestamp_from_datetime(date)))
