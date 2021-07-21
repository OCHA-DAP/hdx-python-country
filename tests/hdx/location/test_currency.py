# -*- coding: UTF-8 -*-
"""Currency Tests"""
from os.path import join

import pytest
from hdx.utilities.dateparse import parse_date

from hdx.location.currency import Currency, CurrencyError


class TestCurrency:
    @pytest.fixture(scope='function')
    def fallback_url(self):
        return 'https://raw.githubusercontent.com/OCHA-DAP/hdx-python-country/master/tests/fixtures/fallbackrates.json'

    def test_get_current_value_in_usd(self, fallback_url):
        Currency.setup()
        assert Currency.get_current_value_in_usd(10, 'usd') == 10
        gbprate = Currency.get_current_value_in_usd(10, 'gbp')
        assert gbprate != 10
        assert Currency.get_current_value_in_currency(gbprate, 'GBP') == 10
        with pytest.raises(CurrencyError):
            Currency.get_current_value_in_usd(10, 'XYZ')
        with pytest.raises(CurrencyError):
            Currency.get_current_value_in_currency(10, 'XYZ')
        Currency.setup(current_rates_url='fail', fallback_rates_url=fallback_url)
        assert Currency.get_current_value_in_usd(10, 'gbp') == 13.844298710126688
        assert Currency.get_current_value_in_currency(10, 'gbp') == 7.223190000000001
        with pytest.raises(CurrencyError):
            Currency.get_current_value_in_usd(10, 'XYZ')
        with pytest.raises(CurrencyError):
            Currency.get_current_value_in_currency(10, 'XYZ')
        with pytest.raises(CurrencyError):
            Currency.setup(current_rates_url='fail')

    def test_get_historic_value_in_usd(self, fallback_url):
        Currency.setup()
        date = parse_date('2020-02-20')
        assert Currency.get_historic_value_in_usd(10, 'USD', date) == 10
        assert Currency.get_historic_value_in_usd(10, 'gbp', date) == 12.877
        assert Currency.get_historic_value_in_currency(10, 'gbp', date) == 7.765783955890346
        with pytest.raises(CurrencyError):
            Currency.get_historic_value_in_usd(10, 'XYZ', date)
        with pytest.raises(CurrencyError):
            Currency.get_historic_value_in_currency(10, 'XYZ', date)
        Currency.setup(historic_rates_url='fail', fallback_to_current=True)
        gbprate = Currency.get_historic_value_in_usd(1, 'gbp', date)
        assert gbprate == Currency.get_current_value_in_usd(1, 'gbp')
        gbprate = Currency.get_historic_value_in_currency(1, 'gbp', date)
        assert gbprate == Currency.get_current_value_in_currency(1, 'gbp')
        Currency.setup(current_rates_url='fail', fallback_rates_url=fallback_url, historic_rates_url='fail', fallback_to_current=True)
        assert Currency.get_historic_value_in_usd(10, 'gbp', date) == 13.844298710126688
        with pytest.raises(CurrencyError):
            Currency.setup(historic_rates_url='fail', fallback_to_current=False)
