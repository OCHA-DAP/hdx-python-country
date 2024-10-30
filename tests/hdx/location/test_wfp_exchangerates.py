from os.path import join

import pytest

from hdx.location import get_int_timestamp
from hdx.location.currency import Currency
from hdx.location.wfp_api import WFPAPI
from hdx.location.wfp_exchangerates import WFPExchangeRates
from hdx.utilities.dateparse import parse_date
from hdx.utilities.downloader import Download
from hdx.utilities.path import temp_dir
from hdx.utilities.retriever import Retrieve


class TestWFPExchangeRates:
    @pytest.fixture(scope="class")
    def currency(self):
        return "afn"

    @pytest.fixture(scope="class")
    def date(self):
        return parse_date("2020-02-20")

    @pytest.fixture(scope="class")
    def fixtures_dir(self):
        return join("tests", "fixtures")

    @pytest.fixture(scope="class")
    def input_dir(self, fixtures_dir):
        return join(fixtures_dir, "wfp")

    def test_wfp_exchangerates(self, input_dir, currency, date):
        with temp_dir(
            "TestWFPExchangeRates",
            delete_on_success=True,
            delete_on_failure=False,
        ) as tempdir:
            with Download(user_agent="test") as downloader:
                retriever = Retrieve(
                    downloader,
                    tempdir,
                    input_dir,
                    tempdir,
                    save=False,
                    use_saved=True,
                )
                wfp_api = WFPAPI(downloader, retriever)
                wfp_api.update_retry_params(attempts=5, wait=5)
                wfp_fx = WFPExchangeRates(wfp_api)
                retry_params = wfp_fx.wfp_api.get_retry_params()
                assert retry_params["attempts"] == 5
                assert retry_params["wait"] == 5
                currencies = wfp_fx.get_currencies()
                assert len(currencies) == 127

                assert (
                    Currency.get_historic_rate(currency, date)
                    == 76.80000305175781
                )
                timestamp = get_int_timestamp(date)
                historic_rates = wfp_fx.get_currency_historic_rates(currency)
                assert historic_rates[timestamp] == 77.01

                all_historic_rates = wfp_fx.get_historic_rates([currency])
                Currency.setup(historic_rates_cache=all_historic_rates)
                assert Currency.get_historic_rate(currency, date) == 77.01
