from datetime import datetime

from hdx.utilities.dateparse import get_timestamp_from_datetime

_cache_timestamp_lookup = {}


def get_int_timestamp(date: datetime) -> int:
    """
    Get integer timestamp from datetime object with caching

    Args:
        date (datetime): datetime object

    Returns:
        int: Integer timestamp
    """
    timestamp = _cache_timestamp_lookup.get(date)
    if timestamp is None:
        timestamp = int(round(get_timestamp_from_datetime(date)))
        _cache_timestamp_lookup[date] = timestamp
    return timestamp
