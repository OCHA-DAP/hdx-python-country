from os import environ

import pytest

from hdx.location import get_int_timestamp
from hdx.location.currency import Currency
from hdx.location.wfp_exchangerates import WfpApiToken, WFPExchangeRates
from hdx.utilities.dateparse import parse_date

if WfpApiToken is not None:

    class TestWFPExchangeRates:
        @pytest.fixture(scope="class")
        def wfp_fx(self):
            key = environ.get("WFP_KEY")
            secret = environ.get("WFP_SECRET")
            return WFPExchangeRates(key, secret)

        @pytest.fixture(scope="class")
        def currency(self):
            return "afn"

        @pytest.fixture(scope="class")
        def date(self):
            return parse_date("2020-02-20")

        def test_get_currencies(self, wfp_fx):
            currencies = wfp_fx.get_currencies()
            assert len(currencies) == 126

        def test_get_historic_rates(self, wfp_fx, currency, date):
            assert (
                Currency.get_historic_rate(currency, date) == 76.80000305175781
            )
            timestamp = get_int_timestamp(date)
            historic_rates = wfp_fx.get_currency_historic_rates(currency)
            assert historic_rates[timestamp] == 77.01

        def test_get_all_historic_rates(self, wfp_fx, currency, date):
            all_historic_rates = wfp_fx.get_historic_rates([currency])
            Currency.setup(historic_rates_cache=all_historic_rates)
            assert Currency.get_historic_rate(currency, date) == 77.01
