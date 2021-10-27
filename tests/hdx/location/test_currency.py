"""Currency Tests"""
from os.path import join

import pytest
from hdx.utilities.dateparse import parse_date
from hdx.utilities.downloader import Download
from hdx.utilities.path import get_temp_dir
from hdx.utilities.retriever import Retrieve
from hdx.utilities.useragent import UserAgent

from hdx.location.currency import Currency, CurrencyError


class TestCurrency:
    @pytest.fixture(scope="class", autouse=True)
    def retrievers(self):
        name = "hdx-python-country-rates"
        UserAgent.set_global(name)
        downloader = Download()
        fallback_dir = join("tests", "fixtures")
        temp_dir = get_temp_dir(name)
        retriever = Retrieve(
            downloader,
            fallback_dir,
            temp_dir,
            temp_dir,
            save=False,
            use_saved=False,
        )
        retriever_broken = Retrieve(
            downloader,
            "tests",
            temp_dir,
            temp_dir,
            save=False,
            use_saved=False,
        )
        yield retriever, retriever_broken
        UserAgent.clear_global()

    def test_get_current_value_in_usd(self, retrievers):
        Currency.setup()
        assert Currency.get_current_value_in_usd(10, "usd") == 10
        assert Currency.get_current_value_in_currency(10, "usd") == 10
        gbprate = Currency.get_current_value_in_usd(10, "gbp")
        assert gbprate != 10
        assert Currency.get_current_value_in_currency(gbprate, "GBP") == 10
        with pytest.raises(CurrencyError):
            Currency.get_current_value_in_usd(10, "XYZ")
        with pytest.raises(CurrencyError):
            Currency.get_current_value_in_currency(10, "XYZ")
        retriever = retrievers[0]
        Currency.setup(
            retriever=retriever,
            current_rates_url="fail",
            fallback_current_to_static=True,
        )
        assert (
            Currency.get_current_value_in_usd(10, "gbp") == 13.844298710126688
        )
        assert (
            Currency.get_current_value_in_currency(10, "gbp")
            == 7.223190000000001
        )
        with pytest.raises(CurrencyError):
            Currency.get_current_value_in_usd(10, "XYZ")
        with pytest.raises(CurrencyError):
            Currency.get_current_value_in_currency(10, "XYZ")
        with pytest.raises(CurrencyError):
            Currency.setup(
                retriever=retriever,
                current_rates_url="fail",
                fallback_current_to_static=False,
            )
        with pytest.raises(CurrencyError):
            Currency.setup(
                retriever=retrievers[1],
                current_rates_url="fail",
                fallback_current_to_static=True,
            )
        Currency._current_rates = None
        assert Currency.get_current_rate("gbp") != 1

    def test_get_historic_value_in_usd(self, retrievers):
        Currency.setup()
        date = parse_date("2020-02-20")
        assert Currency.get_historic_value_in_usd(10, "USD", date) == 10
        assert Currency.get_historic_value_in_currency(10, "usd", date) == 10
        assert Currency.get_historic_value_in_usd(10, "gbp", date) == 12.877
        assert (
            Currency.get_historic_value_in_currency(10, "gbp", date)
            == 7.765783955890346
        )
        with pytest.raises(CurrencyError):
            Currency.get_historic_value_in_usd(10, "XYZ", date)
        with pytest.raises(CurrencyError):
            Currency.get_historic_value_in_currency(10, "XYZ", date)
        Currency.setup(
            historic_rates_url="fail", fallback_historic_to_current=True
        )
        gbprate = Currency.get_historic_value_in_usd(1, "gbp", date)
        assert gbprate == Currency.get_current_value_in_usd(1, "gbp")
        gbprate = Currency.get_historic_value_in_currency(1, "gbp", date)
        assert gbprate == Currency.get_current_value_in_currency(1, "gbp")
        retriever = retrievers[0]
        Currency.setup(
            retriever=retriever,
            current_rates_url="fail",
            historic_rates_url="fail",
            fallback_historic_to_current=True,
            fallback_current_to_static=True,
        )
        assert (
            Currency.get_historic_value_in_usd(10, "gbp", date)
            == 13.844298710126688
        )
        with pytest.raises(CurrencyError):
            Currency.setup(
                retriever=retriever,
                historic_rates_url="fail",
                fallback_historic_to_current=False,
            )
        Currency._historic_rates = None
        assert Currency.get_historic_rate("gbp", date) == 0.7765783955890346
