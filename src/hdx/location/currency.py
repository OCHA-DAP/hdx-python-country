"""Currency conversion"""

import logging
from copy import copy
from datetime import datetime, timezone
from typing import Dict, Optional, Union

from . import get_int_timestamp
from hdx.utilities.dateparse import (
    now_utc,
    parse_date,
)
from hdx.utilities.dictandlist import dict_of_dicts_add
from hdx.utilities.downloader import Download, DownloadError
from hdx.utilities.path import get_temp_dir
from hdx.utilities.retriever import Retrieve

logger = logging.getLogger(__name__)


class CurrencyError(Exception):
    pass


class Currency:
    """Currency class for performing currency conversion. Uses Yahoo, falling back on
    https://github.com/fawazahmed0/currency-api for current rates and Yahoo falling back on IMF for historic
    rates. Note that rate calls are cached.
    """

    _primary_rates_url = "https://query2.finance.yahoo.com/v8/finance/chart/{currency}=X?period1={date}&period2={date}&interval=1d&events=div%2Csplit&formatted=false&lang=en-US&region=US&corsDomain=finance.yahoo.com"
    _secondary_rates_url = "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.min.json"
    _secondary_historic_url = (
        "https://codeforiati.org/imf-exchangerates/imf_exchangerates.csv"
    )
    _cached_current_rates = None
    _cached_historic_rates = None
    _rates_api = None
    _secondary_rates = None
    _secondary_historic = None
    _fallback_to_current = False
    _no_historic = False
    _user_agent = "hdx-python-country-rates"
    _retriever = None
    _log_level = logging.DEBUG
    _fixed_now = None
    _threshold = 1.3

    @classmethod
    def setup(
        cls,
        retriever: Optional[Retrieve] = None,
        primary_rates_url: str = _primary_rates_url,
        secondary_rates_url: str = _secondary_rates_url,
        secondary_historic_url: str = _secondary_historic_url,
        fallback_historic_to_current: bool = False,
        fallback_current_to_static: bool = False,
        no_historic: bool = False,
        fixed_now: Optional[datetime] = None,
        log_level: int = logging.DEBUG,
        current_rates_cache: Dict = {"USD": 1},
        historic_rates_cache: Dict = {},
    ) -> None:
        """
        Setup the sources. If you wish to use a static fallback file by setting
        fallback_current_to_static to True, it needs to be named "secondary_rates.json"
        and put in the fallback_dir of the passed in Retriever.

        Args:
            retriever (Optional[Retrieve]): Retrieve object to use for downloading. Defaults to None (generate a new one).
            primary_rates_url (str): Primary rates url to use. Defaults to Yahoo API.
            secondary_rates_url (str): Current rates url to use. Defaults to currency-api.
            secondary_historic_url (str): Historic rates url to use. Defaults to IMF (via IATI).
            fallback_historic_to_current (bool): If historic unavailable, fallback to current. Defaults to False.
            fallback_current_to_static (bool): Use static file as final fallback. Defaults to False.
            no_historic (bool): Do not set up historic rates. Defaults to False.
            fixed_now (Optional[datetime]): Use a fixed datetime for now. Defaults to None (use datetime.now()).
            log_level (int): Level at which to log messages. Defaults to logging.DEBUG.
            current_rates_cache (Dict): Pre-populate current rates cache with given values. Defaults to {"USD": 1}.
            historic_rates_cache (Dict): Pre-populate historic rates cache with given values. Defaults to {}.

        Returns:
            None
        """

        cls._cached_current_rates = copy(current_rates_cache)
        cls._cached_historic_rates = copy(historic_rates_cache)
        cls._rates_api = primary_rates_url
        cls._secondary_rates = None
        cls._secondary_historic = None
        if retriever is None:
            downloader = Download(user_agent=cls._user_agent)
            temp_dir = get_temp_dir(cls._user_agent)
            retriever = Retrieve(
                downloader,
                None,
                temp_dir,
                temp_dir,
                save=False,
                use_saved=False,
            )
        cls._retriever = retriever
        try:
            secondary_rates = retriever.download_json(
                secondary_rates_url,
                "secondary_rates.json",
                "secondary current exchange rates",
                fallback_current_to_static,
            )
            cls._secondary_rates = secondary_rates["usd"]
        except (DownloadError, OSError):
            logger.exception("Error getting secondary current rates!")
            cls._secondary_rates = "FAIL"
        cls._fixed_now = fixed_now
        cls._log_level = log_level
        if no_historic:
            cls._no_historic = True
        if cls._no_historic:
            return
        try:
            _, iterator = retriever.get_tabular_rows(
                secondary_historic_url,
                dict_form=True,
                filename="historic_rates.csv",
                logstr="secondary historic exchange rates",
            )
            cls._secondary_historic = {}
            for row in iterator:
                currency = row["Currency"]
                date = get_int_timestamp(parse_date(row["Date"]))
                rate = float(row["Rate"])
                dict_of_dicts_add(
                    cls._secondary_historic, currency, date, rate
                )
        except (DownloadError, OSError):
            logger.exception("Error getting secondary historic rates!")
            cls._secondary_historic = "FAIL"
        cls._fallback_to_current = fallback_historic_to_current

    @classmethod
    def _get_primary_rates_data(
        cls, currency: str, timestamp: int, downloader=None
    ) -> Optional[Dict]:
        """
        Get the primary fx rate data for currency

        Args:
            currency (str): Currency
            timestamp (int): Timestamp to use for fx conversion

        Returns:
            Optional[float]: fx rate or None
        """
        if cls._rates_api is None:
            Currency.setup()
        url = cls._rates_api.format(currency=currency, date=str(timestamp))
        if downloader is None:
            downloader = cls._retriever
        try:
            chart = downloader.download_json(url, log_level=cls._log_level)[
                "chart"
            ]
            if chart["error"] is not None:
                return None
            return chart["result"][0]
        except (DownloadError, KeyError):
            return None

    @classmethod
    def _get_adjclose(
        cls, indicators: Dict, currency: str, timestamp: int
    ) -> Optional[float]:
        """
        Get the adjusted close fx rate from the indicators dictionary returned
        from the Yahoo API.

        Args:
            indicators (Dict): Indicators dictionary from Yahoo API
            currency (str): Currency
            timestamp (int): Timestamp to use for fx conversion

        Returns:
            Optional[float]: Adjusted close fx rate or None
        """
        adjclose = indicators["adjclose"][0].get("adjclose")
        if adjclose is None:
            return None

        def beyond_threshold(x, y):
            if max(x, y) / min(x, y) > cls._threshold:
                return True
            return False

        def within_threshold(x, y):
            if max(x, y) / min(x, y) > cls._threshold:
                return False
            return True

        # Compare adjclose to other variables returned by Yahoo API
        adjclose = adjclose[0]
        quote = indicators["quote"][0]
        open = quote.get("open")
        fraction_ok = True
        if open:
            open = open[0]
            if beyond_threshold(adjclose, open):
                fraction_ok = False
        high = quote.get("high")
        if high:
            high = high[0]
            if beyond_threshold(adjclose, high):
                fraction_ok = False
        low = quote.get("low")
        if low:
            low = low[0]
            if beyond_threshold(adjclose, low):
                fraction_ok = False
        if fraction_ok:
            # if no discrepancies, adjclose is ok
            return adjclose

        if cls._no_historic:
            secondary_fx_rate = None
        else:
            secondary_fx_rate = cls._get_secondary_historic_rate(
                currency, timestamp
            )
        if not secondary_fx_rate:
            # compare with high and low to reveal errors from Yahoo feed
            if high and low:
                if within_threshold(low, high):
                    return low + (high - low) / 2
            return None

        # compare with secondary historic rate
        if within_threshold(adjclose, secondary_fx_rate):
            return adjclose
        # if adjclose is wacky, find another value to return that is ok
        if high and low:
            if within_threshold(high, secondary_fx_rate) and within_threshold(
                low, secondary_fx_rate
            ):
                return low + (high - low) / 2
        if open:
            if within_threshold(open, secondary_fx_rate):
                return open
        if high:
            if within_threshold(high, secondary_fx_rate):
                return high
        if low:
            if within_threshold(low, secondary_fx_rate):
                return low
        return secondary_fx_rate

    @classmethod
    def _get_primary_rate(
        cls, currency: str, timestamp: Optional[int] = None
    ) -> Optional[float]:
        """
        Get the primary current fx rate for currency ofr a given timestamp. If no timestamp is supplied,
        datetime.now() will be used unless fixed_now was passed in the constructor.

        Args:
            currency (str): Currency
            timestamp (Optional[int]): Timestamp to use for fx conversion. Defaults to None (datetime.now())

        Returns:
            Optional[float]: fx rate or None
        """
        if timestamp is None:
            if cls._fixed_now:
                now = cls._fixed_now
                get_close = True
            else:
                now = now_utc()
                get_close = False
            timestamp = get_int_timestamp(now)
        else:
            get_close = True
        data = cls._get_primary_rates_data(currency, timestamp)
        if not data:
            return None
        if get_close:
            return cls._get_adjclose(data["indicators"], currency, timestamp)
        return data["meta"]["regularMarketPrice"]

    @classmethod
    def _get_secondary_current_rate(cls, currency: str) -> Optional[float]:
        """
        Get the secondary current fx rate for currency

        Args:
            currency (str): Currency

        Returns:
            Optional[float]: fx rate or None
        """
        if cls._secondary_rates is None:
            Currency.setup()
        if cls._secondary_rates == "FAIL":
            return None
        return cls._secondary_rates.get(currency.lower())

    @classmethod
    def get_current_rate(cls, currency: str) -> float:
        """
        Get the current fx rate for currency

        Args:
            currency (str): Currency

        Returns:
            float: fx rate
        """
        currency = currency.upper()
        if cls._cached_current_rates is None:
            Currency.setup()
        fx_rate = cls._cached_current_rates.get(currency)
        if fx_rate is not None:
            return fx_rate
        fx_rate = cls._get_primary_rate(currency)
        if fx_rate is not None:
            cls._cached_current_rates[currency] = fx_rate
            return fx_rate
        fx_rate = cls._get_secondary_current_rate(currency)
        if fx_rate is not None:
            logger.warning(f"Using secondary current rate for {currency}!")
            cls._cached_current_rates[currency] = fx_rate
            return fx_rate
        raise CurrencyError(f"Failed to get rate for currency {currency}!")

    @classmethod
    def get_current_value_in_usd(
        cls, value: Union[int, float], currency: str
    ) -> float:
        """
        Get the current USD value of the value in local currency

        Args:
            value (Union[int, float]): Value in local currency
            currency (str): Currency

        Returns:
            float: Value in USD
        """
        currency = currency.upper()
        if currency == "USD":
            return value
        fx_rate = cls.get_current_rate(currency)
        return value / fx_rate

    @classmethod
    def get_current_value_in_currency(
        cls, usdvalue: Union[int, float], currency: str
    ) -> float:
        """
        Get the current value in local currency of the value in USD

        Args:
            usdvalue (Union[int, float]): Value in USD
            currency (str): Currency

        Returns:
            float: Value in local currency
        """
        currency = currency.upper()
        if currency == "USD":
            return usdvalue
        fx_rate = cls.get_current_rate(currency)
        return usdvalue * fx_rate

    @classmethod
    def _get_interpolated_rate(
        cls,
        timestamp1: int,
        rate1: float,
        timestamp2: int,
        rate2: float,
        desired_timestamp: int,
    ) -> float:
        """
        Return a rate for a desired timestamp based on linearly interpolating between
        two timestamp/rate pairs.

        Args:
            timestamp1 (int): First timestamp to use for fx conversion
            rate1 (float): Rate at first timestamp
            timestamp2 (int): Second timestamp to use for fx conversion
            rate2 (float): Rate at second timestamp
            desired_timestamp (int): Timestamp at which rate is desired

        Returns:
            float: Rate at desired timestamp
        """
        return rate1 + (desired_timestamp - timestamp1) * (
            (rate2 - rate1) / (timestamp2 - timestamp1)
        )

    @classmethod
    def _get_secondary_historic_rate(
        cls, currency: str, timestamp: int
    ) -> Optional[float]:
        """
        Get the secondary fx rate for currency on a particular date

        Args:
            currency (str): Currency
            timestamp (int): Timestamp to use for fx conversion

        Returns:
            Optional[float]: fx rate or None
        """
        if cls._secondary_historic is None:
            Currency.setup()
        if cls._secondary_historic == "FAIL":
            return None
        currency_data = cls._secondary_historic.get(currency)
        if currency_data is None:
            return None
        fx_rate = currency_data.get(timestamp)
        if fx_rate:
            return fx_rate
        timestamp1 = None
        timestamp2 = None
        for ts in currency_data.keys():
            if timestamp > ts:
                timestamp1 = ts
            else:
                timestamp2 = ts
                break
        if timestamp1 is None:
            if timestamp2 is None:
                return None
            return currency_data[timestamp2]
        if timestamp2 is None:
            return currency_data[timestamp1]
        return cls._get_interpolated_rate(
            timestamp1,
            currency_data[timestamp1],
            timestamp2,
            currency_data[timestamp2],
            timestamp,
        )

    @classmethod
    def get_historic_rate(
        cls, currency: str, date: datetime, ignore_timeinfo: bool = True
    ) -> float:
        """
        Get the fx rate for currency on a particular date. Any time and time zone
        information will be ignored by default (meaning that the time is set to 00:00:00
        and the time zone set to UTC). To have the time and time zone accounted for,
        set ignore_timeinfo to False. This may affect which day's closing value is used.

        Args:
            currency (str): Currency
            date (datetime): Date to use for fx conversion
            ignore_timeinfo (bool): Ignore time and time zone of date. Defaults to True.

        Returns:
            float: fx rate
        """
        currency = currency.upper()
        if currency == "USD":
            return 1
        if cls._cached_historic_rates is None:
            Currency.setup()
        currency_data = cls._cached_historic_rates.get(currency)
        if ignore_timeinfo:
            date = date.replace(
                hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
            )
        else:
            date = date.astimezone(timezone.utc)
        timestamp = get_int_timestamp(date)
        if currency_data is not None:
            fx_rate = currency_data.get(timestamp)
            if fx_rate is not None:
                return fx_rate
        fx_rate = cls._get_primary_rate(currency, timestamp)
        if fx_rate is not None:
            dict_of_dicts_add(
                cls._cached_historic_rates, currency, timestamp, fx_rate
            )
            return fx_rate
        fx_rate = cls._get_secondary_historic_rate(currency, timestamp)
        if fx_rate is not None:
            dict_of_dicts_add(
                cls._cached_historic_rates, currency, timestamp, fx_rate
            )
            return fx_rate
        if cls._fallback_to_current:
            fx_rate = cls.get_current_rate(currency)
            if fx_rate:
                logger.warning(
                    f"Falling back to current rate for currency {currency} on date {date.isoformat()}!"
                )
            return fx_rate
        raise CurrencyError(
            f"Failed to get rate for currency {currency} on date {date.isoformat()}!"
        )

    @classmethod
    def get_historic_value_in_usd(
        cls,
        value: Union[int, float],
        currency: str,
        date: datetime,
        ignore_timeinfo: bool = True,
    ) -> float:
        """
        Get the USD value of the value in local currency on a particular date. Any time
        and time zone information will be ignored by default (meaning that the time is
        set to 00:00:00 and the time zone set to UTC). To have the time and time zone
        accounted for, set ignore_timeinfo to False. This may affect which day's closing
        value is used.

        Args:
            value (Union[int, float]): Value in local currency
            currency (str): Currency
            date (datetime): Date to use for fx conversion
            ignore_timeinfo (bool): Ignore time and time zone of date. Defaults to True.

        Returns:
            float: Value in USD
        """
        currency = currency.upper()
        if currency == "USD":
            return value
        fx_rate = cls.get_historic_rate(
            currency, date, ignore_timeinfo=ignore_timeinfo
        )
        return value / fx_rate

    @classmethod
    def get_historic_value_in_currency(
        cls,
        usdvalue: Union[int, float],
        currency: str,
        date: datetime,
        ignore_timeinfo: bool = True,
    ) -> float:
        """
        Get the current value in local currency of the value in USD on a particular
        date. Any time and time zone information will be ignored by default (meaning
        that the time is set to 00:00:00 and the time zone set to UTC). To have the time
        and time zone accounted for, set ignore_timeinfo to False. This may affect which
        day's closing value is used.

        Args:
            value (Union[int, float]): Value in USD
            currency (str): Currency
            date (datetime): Date to use for fx conversion
            ignore_timeinfo (bool): Ignore time and time zone of date. Defaults to True.

        Returns:
            float: Value in local currency
        """
        currency = currency.upper()
        if currency == "USD":
            return usdvalue
        fx_rate = cls.get_historic_rate(
            currency, date, ignore_timeinfo=ignore_timeinfo
        )
        return usdvalue * fx_rate
