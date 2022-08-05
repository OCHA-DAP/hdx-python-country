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
    @pytest.fixture(scope="class")
    def fixtures(self):
        return join("tests", "fixtures")

    @pytest.fixture(scope="class")
    def secondary_historic_url(self, fixtures):
        return join(fixtures, "secondary_historic_rates.csv")

    @pytest.fixture(scope="class", autouse=True)
    def retrievers(self, fixtures):
        name = "hdx-python-country-rates"
        UserAgent.set_global(name)
        downloader = Download()
        fallback_dir = fixtures
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
        Currency.setup(no_historic=True)
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
            primary_rates_url="fail",
            secondary_rates_url="fail",
            fallback_current_to_static=True,
            no_historic=True,
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
                primary_rates_url="fail",
                secondary_rates_url="fail",
                fallback_current_to_static=False,
                no_historic=True,
            )
            Currency.get_current_value_in_currency(10, "gbp")
        with pytest.raises(CurrencyError):
            Currency.setup(
                retriever=retrievers[1],
                primary_rates_url="fail",
                secondary_rates_url="fail",
                fallback_current_to_static=True,
                no_historic=True,
            )
            Currency.get_current_value_in_currency(10, "gbp")
        Currency._rates_api = None
        assert Currency.get_current_rate("usd") == 1
        rate1 = Currency.get_current_rate("gbp")
        assert rate1 != 1
        Currency.setup(
            retriever=retrievers[1],
            primary_rates_url="fail",
            secondary_rates_url="fail",
            fallback_current_to_static=False,
            no_historic=True,
        )
        Currency._secondary_rates = None
        rate2 = Currency.get_current_rate("gbp")
        assert rate2 != 1
        assert (rate1 - rate2) / rate1 < 0.002

    def test_get_historic_value_in_usd(
        self, retrievers, secondary_historic_url
    ):
        Currency._no_historic = False
        Currency.setup(secondary_historic_url=secondary_historic_url)
        date = parse_date("2020-02-20").replace(tzinfo=None)
        assert Currency.get_historic_rate("usd", date) == 1
        assert Currency.get_historic_value_in_usd(10, "USD", date) == 10
        assert Currency.get_historic_value_in_currency(10, "usd", date) == 10
        assert Currency.get_historic_rate("gbp", date) == 0.76910001039505
        assert (
            Currency.get_historic_value_in_usd(10, "gbp", date)
            == 13.002210200027791
        )
        assert (
            Currency.get_historic_value_in_currency(10, "gbp", date)
            == 7.6910001039505005
        )
        with pytest.raises(CurrencyError):
            Currency.get_historic_value_in_usd(10, "XYZ", date)
        with pytest.raises(CurrencyError):
            Currency.get_historic_value_in_currency(10, "XYZ", date)
        Currency.setup(
            primary_rates_url="fail",
            secondary_historic_url="fail",
            fallback_historic_to_current=True,
        )
        gbprate = Currency.get_historic_value_in_usd(1, "gbp", date)
        assert gbprate == Currency.get_current_value_in_usd(1, "gbp")
        gbprate = Currency.get_historic_value_in_currency(1, "gbp", date)
        assert gbprate == Currency.get_current_value_in_currency(1, "gbp")
        retriever = retrievers[0]
        Currency.setup(
            retriever=retriever,
            primary_rates_url="fail",
            secondary_rates_url="fail",
            secondary_historic_url="fail",
            fallback_historic_to_current=True,
            fallback_current_to_static=True,
        )
        assert (
            Currency.get_historic_value_in_usd(10, "gbp", date)
            == 13.844298710126688
        )
        Currency.setup(
            retriever=retriever,
            secondary_historic_url=secondary_historic_url,
            primary_rates_url="fail",
            secondary_rates_url="fail",
            fallback_historic_to_current=False,
            fallback_current_to_static=False,
        )
        assert (
            Currency.get_historic_rate("gbp", parse_date("2010-02-20"))
            == 0.762107990702283
        )
        assert (
            Currency.get_historic_rate("gbp", parse_date("2030-02-20"))
            == 0.809028760972452
        )
        assert (
            Currency.get_historic_rate("gbp", parse_date("2020-01-31"))
            == 0.761817697025102
        )
        with pytest.raises(CurrencyError):
            Currency.setup(
                retriever=retriever,
                primary_rates_url="fail",
                secondary_historic_url="fail",
                fallback_historic_to_current=False,
            )
            Currency.get_historic_value_in_usd(10, "gbp", date)
        Currency._secondary_historic = None
        # Interpolation
        # 0.761817697025102 + (0.776276975624903 - 0.761817697025102) * 20 / 29
        # 0.761817697025102 + (0.776276975624903 - 0.761817697025102) * (1582156800-1580428800) / (1582934400 - 1580428800)
        assert Currency.get_historic_rate("gbp", date) == 0.7717896133008268
