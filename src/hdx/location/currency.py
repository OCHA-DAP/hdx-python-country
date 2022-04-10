"""Currency conversion"""
import logging
from datetime import datetime
from typing import Optional, Union

import exchangerates
from hdx.utilities.downloader import Download, DownloadError
from hdx.utilities.path import get_temp_dir
from hdx.utilities.retriever import Retrieve

logger = logging.getLogger(__name__)


class CurrencyError(Exception):
    pass


class Currency:
    """Currency class for performing currency conversion"""

    _current_rates_url = "https://api.exchangerate.host/latest?base=usd"
    _historic_rates_url = (
        "https://codeforiati.org/exchangerates-scraper/consolidated.csv"
    )
    _current_rates = None
    _historic_rates = None
    _fallback_to_current = False

    @classmethod
    def setup(
        cls,
        retriever: Optional[Retrieve] = None,
        current_rates_url: str = _current_rates_url,
        historic_rates_url: str = _historic_rates_url,
        fallback_historic_to_current: bool = False,
        fallback_current_to_static: bool = False,
    ) -> None:
        """
        Get the current USD value of the value in local currency

        Args:
            retriever (Optional[Retrieve]): Retrieve object to use for downloading. Defaults to None (generate a new one).
            current_rates_url (str): Current rates url to use. Defaults to https://api.exchangerate.host/latest?base=usd.
            historic_rates_url (str): Historic rates url to use. Defaults to https://codeforiati.org/exchangerates-scraper/consolidated.csv.
            fallback_historic_to_current (bool): Whether to try getting current USD value if historic is not available.
            fallback_current_to_static (bool): Whether to use USD value from static file if current is not available.

        Returns:
            None
        """

        cls._current_rates = None
        cls._historic_rates = None
        if retriever is None:
            name = "hdx-python-country-rates"
            downloader = Download(user_agent=name)
            temp_dir = get_temp_dir(name)
            retriever = Retrieve(
                downloader,
                None,
                temp_dir,
                temp_dir,
                save=False,
                use_saved=False,
            )
        else:
            downloader = None
        try:
            current_rates = retriever.download_json(
                current_rates_url,
                "currentrates.json",
                "current exchange rates",
                fallback_current_to_static,
            )
            cls._current_rates = current_rates["rates"]
        except (DownloadError, OSError) as ex:
            raise CurrencyError("Error getting current rates!") from ex
        try:
            rates_path = retriever.download_file(
                historic_rates_url,
                "rates.csv",
                "historic exchange rates",
                False,
            )
            cls._historic_rates = exchangerates.CurrencyConverter(
                update=False, source=rates_path
            )
        except (DownloadError, OSError) as ex:
            if fallback_historic_to_current:
                logger.warning(
                    "Falling back to current rates for all historic rates!"
                )
            else:
                raise CurrencyError("Error getting historic rates!") from ex
        cls._fallback_to_current = fallback_historic_to_current
        if downloader:
            downloader.close()

    @classmethod
    def get_current_rate(cls, currency: str) -> float:
        """
        Get the current fx rate for currency

        Args:
            currency (str): Currency

        Returns:
            float: fx rate
        """
        if cls._current_rates is None:
            Currency.setup()
        currency = currency.upper()
        fx_rate = cls._current_rates.get(currency)
        if fx_rate is None:
            raise CurrencyError(f"Currency {currency} is invalid!")
        return fx_rate

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
    def get_historic_rate(cls, currency, date):
        """
        Get the fx rate for currency on a particular date

        Args:
            currency (str): Currency

        Returns:
            float: fx rate
        """
        if cls._historic_rates is None:
            Currency.setup()
        currency = currency.upper()
        return cls._historic_rates.closest_rate(currency, date.date())[
            "conversion_rate"
        ]

    @classmethod
    def get_historic_value_in_usd(
        cls, value: Union[int, float], currency: str, date: datetime
    ) -> float:
        """
        Get the USD value of the value in local currency on a particular date

        Args:
            value (Union[int, float]): Value in local currency
            currency (str): Currency
            date (datetime): Date to use for fx conversion

        Returns:
            float: Value in USD
        """
        currency = currency.upper()
        if currency == "USD":
            return value
        if cls._historic_rates:
            try:
                fx_rate = cls.get_historic_rate(currency, date)
                return value / fx_rate
            except exchangerates.UnknownCurrencyException:
                pass
        if cls._fallback_to_current:
            return cls.get_current_value_in_usd(value, currency)
        raise CurrencyError(f"Currency {currency} is invalid!")

    @classmethod
    def get_historic_value_in_currency(
        cls, usdvalue: Union[int, float], currency: str, date: datetime
    ) -> float:
        """
        Get the current value in local currency of the value in USD on a particular date

        Args:
            value (Union[int, float]): Value in USD
            currency (str): Currency
            date (datetime): Date to use for fx conversion

        Returns:
            float: Value in local currency
        """
        currency = currency.upper()
        if currency == "USD":
            return usdvalue
        if cls._historic_rates:
            try:
                fx_rate = cls.get_historic_rate(currency, date)
                return usdvalue * fx_rate
            except exchangerates.UnknownCurrencyException:
                pass
        if cls._fallback_to_current:
            return cls.get_current_value_in_currency(usdvalue, currency)
        raise CurrencyError(f"Currency {currency} is invalid!")
