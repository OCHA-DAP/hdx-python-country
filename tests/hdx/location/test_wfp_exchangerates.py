from hdx.location.currency import Currency
from hdx.location.int_timestamp import get_int_timestamp
from hdx.location.wfp_api import WFPAPI
from hdx.location.wfp_exchangerates import WFPExchangeRates
from hdx.utilities.dateparse import parse_date
from hdx.utilities.downloader import Download
from hdx.utilities.path import temp_dir
from hdx.utilities.retriever import Retrieve


class TestWFPExchangeRates:
    def test_wfp_exchangerates(self, reset_currency, input_dir):
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
                currency = "afn"
                date = parse_date("2020-02-20")
                wfp_api = WFPAPI(downloader, retriever)
                wfp_api.update_retry_params(attempts=5, wait=5)
                wfp_fx = WFPExchangeRates(wfp_api)
                retry_params = wfp_fx.wfp_api.get_retry_params()
                assert retry_params["attempts"] == 5
                assert retry_params["wait"] == 5
                currenciesinfo = wfp_fx.get_currencies_info()
                assert len(currenciesinfo) == 127
                currencies = wfp_fx.get_currencies()
                assert len(currencies) == 127

                Currency.setup()
                assert Currency.get_historic_rate(currency, date) == 76.80000305175781
                timestamp = get_int_timestamp(date)
                historic_rates = wfp_fx.get_currency_historic_rates(currency)
                keys = list(historic_rates.keys())
                sorted_keys = sorted(keys)
                assert keys == sorted_keys
                assert historic_rates[timestamp] == 77.01

                all_historic_rates = wfp_fx.get_historic_rates([currency])
                Currency.setup(
                    historic_rates_cache=all_historic_rates,
                    secondary_historic_rates=all_historic_rates,
                    use_secondary_historic=True,
                )
                assert Currency.get_historic_rate(currency, date) == 77.01
                date = parse_date("2020-02-21")
                assert Currency.get_historic_rate(currency, date) == 77.01
                date = parse_date("2020-02-20 12:00:00")
                assert Currency.get_historic_rate(currency, date) == 77.01
                assert (
                    Currency.get_historic_rate(currency, date, ignore_timeinfo=False)
                    == 77.01
                )
