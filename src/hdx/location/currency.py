# -*- coding: utf-8 -*-
"""Currency conversion"""
import logging
from datetime import datetime
from typing import Union, Optional

import exchangerates
from hdx.utilities import raisefrom
from hdx.utilities.downloader import Download, DownloadError


logger = logging.getLogger(__name__)


class CurrencyError(Exception):
    pass


class Currency(object):
    """Currency class for performing currency conversion"""
    _current_rates_url = 'https://api.exchangerate.host/latest?base=usd'
    _historic_rates_url = 'https://codeforiati.org/exchangerates-scraper/consolidated.csv'
    _current_rates = None
    _historic_rates = None
    _fallback_to_current = False

    @classmethod
    def setup(cls, current_rates_url=_current_rates_url, fallback_rates_url=None, historic_rates_url=_historic_rates_url, fallback_to_current=False):
        # type: (str, Optional[str], str, bool) -> None
        """
        Get the current USD value of the value in local currency

        Args:
            current_rates_url (str): Current rates url to use. Defaults to https://api.exchangerate.host/latest?base=usd.
            fallback_current_url (str): Fallback rates url to use for current rates. Defaults to None.
            historic_rates_url (str): Historic rates url to use. Defaults to https://codeforiati.org/exchangerates-scraper/consolidated.csv.
            fallback_to_current (bool): Whether to try getting current USD value if historic is not available.

        Returns:
            None
        """

        cls._current_rates = None
        cls._historic_rates = None
        with Download(user_agent='fx') as downloader:
            try:
                downloader.download(current_rates_url)
                cls._current_rates = downloader.get_json()['rates']
            except DownloadError as ex:
                if fallback_rates_url:
                    try:
                        downloader.download(fallback_rates_url)
                        cls._current_rates = downloader.get_json()['rates']
                        logger.warning('Using fallback rates!')
                    except DownloadError as ex:
                        raisefrom(CurrencyError, 'Error getting fallback rates from %s!' % fallback_rates_url, ex)
                else:
                    raisefrom(CurrencyError, 'Error getting current rates from %s!' % current_rates_url, ex)
            try:
                rates_path = downloader.download_file(historic_rates_url)
                cls._historic_rates = exchangerates.CurrencyConverter(update=False, source=rates_path)
            except (DownloadError, OSError) as ex:
                if fallback_to_current:
                    logger.warning('Falling back to current rates for all historic rates!')
                else:
                    raisefrom(CurrencyError, 'Error getting historic rates from %s!' % historic_rates_url, ex)
        cls._fallback_to_current = fallback_to_current

    @classmethod
    def get_current_rate(cls, currency):
        # type: (str) -> float
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
            raise CurrencyError('Currency %s is invalid!' % currency)
        return fx_rate

    @classmethod
    def get_current_value_in_usd(cls, value, currency):
        # type: (Union[int, float], str) -> float
        """
        Get the current USD value of the value in local currency

        Args:
            value (Union[int, float]): Value in local currency
            currency (str): Currency

        Returns:
            float: Value in USD
        """
        currency = currency.upper()
        if currency == 'USD':
            return value
        fx_rate = cls.get_current_rate(currency)
        return value / fx_rate

    @classmethod
    def get_current_value_in_currency(cls, usdvalue, currency):
        # type: (Union[int, float], str) -> float
        """
        Get the current value in local currency of the value in USD

        Args:
            usdvalue (Union[int, float]): Value in USD
            currency (str): Currency

        Returns:
            float: Value in local currency
        """
        currency = currency.upper()
        if currency == 'USD':
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
        return cls._historic_rates.closest_rate(currency, date.date())['conversion_rate']

    @classmethod
    def get_historic_value_in_usd(cls, value, currency, date):
        # type: (Union[int, float], str, datetime) -> float
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
        if currency == 'USD':
            return value
        if cls._historic_rates:
            try:
                fx_rate = cls.get_historic_rate(currency, date)
                return value / fx_rate
            except exchangerates.UnknownCurrencyException:
                pass
        if cls._fallback_to_current:
            return cls.get_current_value_in_usd(value, currency)
        raise CurrencyError('Currency %s is invalid!' % currency)

    @classmethod
    def get_historic_value_in_currency(cls, usdvalue, currency, date):
        # type: (Union[int, float], str, datetime) -> float
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
        if currency == 'USD':
            return usdvalue
        if cls._historic_rates:
            try:
                fx_rate = cls.get_historic_rate(currency, date)
                return usdvalue * fx_rate
            except exchangerates.UnknownCurrencyException:
                pass
        if cls._fallback_to_current:
            return cls.get_current_value_in_currency(usdvalue, currency)
        raise CurrencyError('Currency %s is invalid!' % currency)
