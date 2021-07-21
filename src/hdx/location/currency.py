# -*- coding: utf-8 -*-
"""Currency conversion"""
from datetime import datetime
from typing import Union, Optional

import exchangerates
from hdx.utilities import raisefrom
from hdx.utilities.downloader import Download, DownloadError


class CurrencyError(Exception):
    pass


class Currency(object):
    """Currency class for performing currency conversion"""
    _current_rates_url = 'https://api.exchangerate.host/latest?base=usd'
    _historic_rates_url = 'https://codeforiati.org/exchangerates-scraper/consolidated.csv'
    _current_rates = None
    _historic_rates = None

    @classmethod
    def get_current_value_in_usd(cls, value, currency, rates_url=_current_rates_url, fallback_url=None):
        # type: (Union[int, float], str, str, Optional[str]) -> float
        """
        Get the current USD value of the value in local currency

        Args:
            value (Union[int, float]): Value in local currency
            currency (str): Currency
            rates_url (str): Rates url to use. Defaults to https://api.exchangerate.host/latest?base=usd.
            fallback_url (str): Fallback rates url to use. Defaults to None.

        Returns:
            float: Value in USD
        """
        currency = currency.upper()
        if currency == 'USD':
            return value
        if cls._current_rates is None:
            with Download(user_agent='fx') as downloader:
                try:
                    downloader.download(rates_url)
                    cls._current_rates = downloader.get_json()['rates']
                except DownloadError as ex:
                    if fallback_url:
                        try:
                            downloader.download(fallback_url)
                            cls._current_rates = downloader.get_json()['rates']
                        except DownloadError as ex:
                            raisefrom(CurrencyError, 'Error getting fallback rates from %s!' % fallback_url, ex)
                    else:
                        raisefrom(CurrencyError, 'Error getting current rates from %s!' % rates_url, ex)
        fx_rate = cls._current_rates.get(currency)
        if fx_rate is not None:
            return value / fx_rate
        raise CurrencyError('Currency %s is invalid!' % currency)

    @classmethod
    def get_historic_value_in_usd(cls, value, currency, date, historic_rates_url=_historic_rates_url,
                                  current_rates_url=_current_rates_url, fallback_to_current=False, fallback_current_url=None):
        # type: (Union[int, float], str, datetime, str, str, bool, Optional[str]) -> float
        """
        Get the USD value of the value in local currency on a particular date

        Args:
            value (Union[int, float]): Value in local currency
            currency (str): Currency
            date (datetime): Date to use for fx conversion
            historic_rates_url (str): Historic rates url to use. Defaults to https://codeforiati.org/exchangerates-scraper/consolidated.csv.
            current_rates_url (str): Current rates url to use. Defaults to https://api.exchangerate.host/latest?base=usd.
            fallback_to_current (bool): Whether to try getting current USD value if historic is not available.
            fallback_current_url (str): Fallback rates url to use for current rates. Defaults to None.

        Returns:
            float: Value in USD
        """
        currency = currency.upper()
        if currency == 'USD':
            return value
        if cls._historic_rates is None:
            with Download(user_agent='fx') as downloader:
                try:
                    rates_path = downloader.download_file(historic_rates_url)
                    cls._historic_rates = exchangerates.CurrencyConverter(update=False, source=rates_path)
                except (DownloadError, OSError) as ex:
                    if fallback_to_current:
                        return cls.get_current_value_in_usd(value, currency, rates_url=current_rates_url,
                                                            fallback_url=fallback_current_url)
                    raisefrom(CurrencyError, 'Error getting historic rates from %s!' % historic_rates_url, ex)
        try:
            fx_rate = cls._historic_rates.closest_rate(currency, date.date()).get('conversion_rate')
            return value / fx_rate
        except exchangerates.UnknownCurrencyException as ex:
            if fallback_to_current:
                return cls.get_current_value_in_usd(value, currency, rates_url=current_rates_url, fallback_url=fallback_current_url)
            raisefrom(CurrencyError, 'Currency %s is invalid!' % currency, ex)
