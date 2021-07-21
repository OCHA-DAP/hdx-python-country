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
        assert Currency.get_current_value_in_usd(10, 'usd') == 10
        gbprate = Currency.get_current_value_in_usd(1, 'gbp')
        assert gbprate != 1
        assert Currency.get_current_value_in_usd(10/gbprate, 'GBP') == 10
        with pytest.raises(CurrencyError):
            Currency.get_current_value_in_usd(10, 'XYZ')
        Currency._current_rates = None
        assert Currency.get_current_value_in_usd(10, 'gbp', rates_url='fail', fallback_url=fallback_url) == 13.844298710126688

    def test_get_historic_value_in_usd(self, fallback_url):
        date = parse_date('2020-02-20')
        assert Currency.get_historic_value_in_usd(10, 'USD', date) == 10
        assert Currency.get_historic_value_in_usd(10, 'gbp', date) == 12.877
        with pytest.raises(CurrencyError):
            Currency.get_historic_value_in_usd(10, 'XYZ', date)
        Currency._historic_rates = None
        gbprate = Currency.get_historic_value_in_usd(1, 'gbp', date, historic_rates_url='fail', fallback_to_current=True)
        assert gbprate == Currency.get_current_value_in_usd(1, 'gbp')
        Currency._historic_rates = None
        Currency._current_rates = None
        assert Currency.get_historic_value_in_usd(10, 'gbp', date, historic_rates_url='fail', current_rates_url='fail',
                                                  fallback_to_current=True, fallback_current_url=fallback_url) == 13.844298710126688
