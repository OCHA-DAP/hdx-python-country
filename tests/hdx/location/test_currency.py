"""Currency Tests"""

from os.path import join

import pytest

from hdx.location import get_int_timestamp
from hdx.location.currency import Currency, CurrencyError
from hdx.utilities.dateparse import parse_date
from hdx.utilities.downloader import Download
from hdx.utilities.path import get_temp_dir
from hdx.utilities.retriever import Retrieve
from hdx.utilities.useragent import UserAgent


class TestCurrency:
    @pytest.fixture(scope="class")
    def fixtures(self):
        return join("tests", "fixtures")

    @pytest.fixture(scope="class")
    def secondary_rates_url(self, fixtures):
        return join(fixtures, "secondary_rates.json")

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

    def test_get_current_value_in_usd(self, retrievers, secondary_rates_url):
        Currency.setup(no_historic=True)
        assert Currency.get_current_value_in_usd(10, "usd") == 10
        assert Currency.get_current_value_in_currency(10, "usd") == 10
        gbprate = Currency.get_current_value_in_usd(10, "gbp")
        assert gbprate != 10
        assert Currency.get_current_value_in_currency(gbprate, "GBP") == 10
        xdrrate = Currency.get_current_value_in_usd(10, "xdr")
        assert xdrrate != 10
        assert Currency.get_current_value_in_currency(xdrrate, "xdr") == 10
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
            Currency.get_current_value_in_usd(10, "gbp") == 12.076629158709528
        )
        assert (
            Currency.get_current_value_in_currency(10, "gbp")
            == 8.280456299999999
        )
        with pytest.raises(CurrencyError):
            Currency.get_current_value_in_usd(10, "XYZ")
        with pytest.raises(CurrencyError):
            Currency.get_current_value_in_currency(10, "XYZ")
        Currency.setup(
            no_historic=True,
            primary_rates_url="fail",
            secondary_rates_url=secondary_rates_url,
        )
        xdrrate = Currency.get_current_value_in_usd(10, "xdr")
        assert xdrrate == 13.075473660667791
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
        rate1gbp = Currency.get_current_rate("gbp")
        assert rate1gbp != 1
        rate1xdr = Currency.get_current_rate("xdr")
        assert rate1xdr != 1
        Currency.setup(
            retriever=retrievers[1],
            primary_rates_url="fail",
            secondary_rates_url="fail",
            fallback_current_to_static=False,
            no_historic=True,
        )
        Currency._secondary_rates = None
        rate2gbp = Currency.get_current_rate("gbp")
        assert rate2gbp != 1
        assert abs(rate1gbp - rate2gbp) / rate1gbp < 0.008
        Currency.setup(
            retriever=retrievers[1],
            primary_rates_url="fail",
            secondary_rates_url="fail",
            fallback_current_to_static=False,
            no_historic=True,
        )
        Currency._secondary_rates = None
        rate2xdr = Currency.get_current_rate("xdr")
        assert rate2xdr != 1
        assert abs(rate1xdr - rate2xdr) / rate1xdr < 0.1

    def test_get_current_value_in_usd_fixednnow(
        self, retrievers, secondary_rates_url
    ):
        date = parse_date("2020-02-20")
        Currency.setup(
            no_historic=True,
            fixed_now=date,
            secondary_rates_url=secondary_rates_url,
        )
        assert Currency.get_current_rate("usd") == 1
        assert Currency.get_current_value_in_usd(10, "USD") == 10
        assert Currency.get_current_value_in_currency(10, "usd") == 10
        assert Currency.get_current_rate("gbp") == 0.7735000252723694
        # falls back to secondary current rates
        assert Currency.get_current_rate("xdr") == 0.76479065

    def test_get_historic_value_in_usd(
        self, retrievers, secondary_historic_url
    ):
        Currency._no_historic = False
        Currency.setup(secondary_historic_url=secondary_historic_url)
        date = parse_date("2020-02-20")
        assert Currency.get_historic_rate("usd", date) == 1
        assert Currency.get_historic_value_in_usd(10, "USD", date) == 10
        assert Currency.get_historic_value_in_currency(10, "usd", date) == 10
        assert Currency.get_historic_rate("gbp", date) == 0.7735000252723694
        # falls back to secondary historic rates
        assert Currency.get_historic_rate("xdr", date) == 0.7275806206896552
        assert (
            Currency.get_historic_rate(
                "gbp",
                parse_date("2020-02-20 00:00:00 NZST", timezone_handling=2),
                ignore_timeinfo=False,
            )
            == 0.76910001039505
        )
        assert (
            Currency.get_historic_rate(
                "gbp",
                parse_date("2020-02-19"),
            )
            == 0.76910001039505
        )
        assert (
            Currency.get_historic_value_in_usd(10, "gbp", date)
            == 12.928247799964508
        )
        assert (
            Currency.get_historic_value_in_currency(10, "gbp", date)
            == 7.735000252723694
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
            == 12.076629158709528
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
            == 0.663042036865137
        )
        assert (
            Currency.get_historic_rate("gbp", parse_date("2030-02-20"))
            == 0.745156482861401
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

    def test_broken_rates_no_secondary(self, retrievers):
        Currency._no_historic = False
        Currency.setup(secondary_historic_url="fail")
        # Without the checking against high and low returned by Yahoo API, this
        # returned 3.140000104904175
        assert (
            Currency.get_historic_rate("NGN", parse_date("2017-02-15"))
            == 314.5
        )
        # Without the checking against high and low returned by Yahoo API, this
        # returned 0.10000000149011612
        assert (
            Currency.get_historic_rate("YER", parse_date("2016-09-15"))
            == 249.7249984741211
        )

        # This adjclose value which is the same as the low is wrong!
        # The high and open are very different so exception is raised
        with pytest.raises(CurrencyError):
            Currency.get_historic_rate("COP", parse_date("2015-12-15"))
        # Since the adjclose is not too different from the low and high,
        # despite being outside their range, we use adjclose
        assert (
            Currency.get_historic_rate("XAF", parse_date("2022-04-14"))
            == 605.5509643554688
        )
        # Since the adjclose is not too different from the low and high,
        # despite being outside their range, we use adjclose
        assert (
            Currency.get_historic_rate("XAF", parse_date("2022-04-15"))
            == 601.632568359375
        )

    def test_broken_rates_with_secondary(
        self, retrievers, secondary_historic_url
    ):
        Currency._no_historic = False
        Currency.setup(secondary_historic_url=secondary_historic_url)
        # Without the checking against secondary historic rate, this
        # returned 3.140000104904175
        assert (
            Currency.get_historic_rate("NGN", parse_date("2017-02-15"))
            == 314.5
        )
        # Without the checking against secondary historic rate, this
        # returned 0.10000000149011612
        assert (
            Currency.get_historic_rate("YER", parse_date("2016-09-15"))
            == 249.7249984741211
        )
        # Without the checking against secondary historic rate, this
        # returned 33.13999938964844
        assert (
            Currency.get_historic_rate("COP", parse_date("2015-12-15"))
            == 3269.199951171875
        )

        # Since the adjclose is not too different from the secondary historic
        # rate, we use adjclose
        assert (
            Currency.get_historic_rate("XAF", parse_date("2022-04-14"))
            == 605.5509643554688
        )
        # Since the adjclose is not too different from the secondary historic
        # rate, we use adjclose
        assert (
            Currency.get_historic_rate("XAF", parse_date("2022-04-15"))
            == 601.632568359375
        )

    def test_get_adjclose(self, retrievers, secondary_historic_url):
        Currency._no_historic = False
        Currency.setup(secondary_historic_url="fail")
        indicators = {
            "adjclose": [{"adjclose": [3.140000104904175]}],
            "quote": [
                {
                    "close": [3.140000104904175],
                    "high": [315.0],
                    "low": [314.0],
                    "open": [315.0],
                    "volume": [0],
                }
            ],
        }
        timestamp = get_int_timestamp(parse_date("2017-02-15"))
        assert Currency._get_adjclose(indicators, "NGN", timestamp) == 314.5
        indicators = {
            "adjclose": [{"adjclose": [33.13999938964844]}],
            "quote": [
                {
                    "close": [33.13999938964844],
                    "high": [3320.0],
                    "low": [33.13999938964844],
                    "open": [3269.199951171875],
                    "volume": [0],
                }
            ],
        }
        timestamp = get_int_timestamp(parse_date("2015-12-15"))
        assert Currency._get_adjclose(indicators, "COP", timestamp) is None
        indicators = {
            "adjclose": [{"adjclose": [605.5509643554688]}],
            "quote": [
                {
                    "close": [605.5509643554688],
                    "high": [602.6080932617188],
                    "low": [601.632568359375],
                    "open": [602.6080932617188],
                    "volume": [0],
                }
            ],
        }
        timestamp = get_int_timestamp(parse_date("2022-04-14"))
        assert (
            Currency._get_adjclose(indicators, "XAF", timestamp)
            == 605.5509643554688
        )
        indicators = {
            "adjclose": [{"adjclose": [601.632568359375]}],
            "quote": [
                {
                    "close": [601.632568359375],
                    "high": [606.8197631835938],
                    "low": [606.8197631835938],
                    "open": [606.8197631835938],
                    "volume": [0],
                }
            ],
        }
        timestamp = get_int_timestamp(parse_date("2022-04-15"))
        assert (
            Currency._get_adjclose(indicators, "XAF", timestamp)
            == 601.632568359375
        )
        indicators = {
            "adjclose": [{"adjclose": [314.0000104904175]}],
            "quote": [
                {
                    "close": [314.0000104904175],
                    "high": [3.150],
                    "low": [3.140],
                    "open": [3.150],
                    "volume": [0],
                }
            ],
        }
        timestamp = get_int_timestamp(parse_date("2017-02-15"))
        assert Currency._get_adjclose(indicators, "XXX", timestamp) == 3.145

        Currency.setup(secondary_historic_url=secondary_historic_url)
        indicators = {
            "adjclose": [{"adjclose": [3.140000104904175]}],
            "quote": [
                {
                    "close": [3.140000104904175],
                    "high": [315.0],
                    "low": [314.0],
                    "open": [315.0],
                    "volume": [0],
                }
            ],
        }
        timestamp = get_int_timestamp(parse_date("2017-02-15"))
        assert Currency._get_adjclose(indicators, "NGN", timestamp) == 314.5
        indicators = {
            "adjclose": [{"adjclose": [33.13999938964844]}],
            "quote": [
                {
                    "close": [33.13999938964844],
                    "high": [3320.0],
                    "low": [33.13999938964844],
                    "open": [3269.199951171875],
                    "volume": [0],
                }
            ],
        }
        timestamp = get_int_timestamp(parse_date("2015-12-15"))
        assert (
            Currency._get_adjclose(indicators, "COP", timestamp)
            == 3269.199951171875
        )
        indicators = {
            "adjclose": [{"adjclose": [605.5509643554688]}],
            "quote": [
                {
                    "close": [605.5509643554688],
                    "high": [602.6080932617188],
                    "low": [601.632568359375],
                    "open": [602.6080932617188],
                    "volume": [0],
                }
            ],
        }
        timestamp = get_int_timestamp(parse_date("2022-04-14"))
        assert (
            Currency._get_adjclose(indicators, "XAF", timestamp)
            == 605.5509643554688
        )
        indicators = {
            "adjclose": [{"adjclose": [601.632568359375]}],
            "quote": [
                {
                    "close": [601.632568359375],
                    "high": [606.8197631835938],
                    "low": [606.8197631835938],
                    "open": [606.8197631835938],
                    "volume": [0],
                }
            ],
        }
        timestamp = get_int_timestamp(parse_date("2022-04-15"))
        assert (
            Currency._get_adjclose(indicators, "XAF", timestamp)
            == 601.632568359375
        )
        indicators = {
            "adjclose": [{"adjclose": [314.0000104904175]}],
            "quote": [
                {
                    "close": [314.0000104904175],
                    "high": [3.150],
                    "low": [3.140],
                    "open": [3.150],
                    "volume": [0],
                }
            ],
        }
        timestamp = get_int_timestamp(parse_date("2017-02-15"))
        assert Currency._get_adjclose(indicators, "XXX", timestamp) == 3.145
        indicators = {
            "adjclose": [{"adjclose": [33.13999938964844]}],
            "quote": [
                {
                    "close": [33.13999938964844],
                    "high": [3320.0],
                    "low": [33.13999938964844],
                    "open": [33.199951171875],
                    "volume": [0],
                }
            ],
        }
        timestamp = get_int_timestamp(parse_date("2015-12-15"))
        assert Currency._get_adjclose(indicators, "COP", timestamp) == 3320.0
        indicators = {
            "adjclose": [{"adjclose": [33.13999938964844]}],
            "quote": [
                {
                    "close": [33.13999938964844],
                    "high": [33.200],
                    "low": [3313.999938964844],
                    "open": [33.199951171875],
                    "volume": [0],
                }
            ],
        }
        timestamp = get_int_timestamp(parse_date("2015-12-15"))
        assert (
            Currency._get_adjclose(indicators, "COP", timestamp)
            == 3313.999938964844
        )
        # Everything is wacky but the values are in the same order of magnitude
        # as each other so adjclose is assumed to be ok
        indicators = {
            "adjclose": [{"adjclose": [33.13999938964844]}],
            "quote": [
                {
                    "close": [33.13999938964844],
                    "high": [33.200],
                    "low": [33.999938964844],
                    "open": [33.199951171875],
                    "volume": [0],
                }
            ],
        }
        timestamp = get_int_timestamp(parse_date("2015-12-15"))
        assert (
            Currency._get_adjclose(indicators, "COP", timestamp)
            == 33.13999938964844
        )
        # Everything is wacky and the values are not in the same order of
        # magnitude as each other so secondary historic rate is returned
        indicators = {
            "adjclose": [{"adjclose": [333.13999938964844]}],
            "quote": [
                {
                    "close": [333.13999938964844],
                    "high": [33333.200],
                    "low": [3.999938964844],
                    "open": [33.199951171875],
                    "volume": [0],
                }
            ],
        }
        timestamp = get_int_timestamp(parse_date("2015-12-15"))
        assert (
            Currency._get_adjclose(indicators, "COP", timestamp)
            == 3124.504838709677
        )
        # Everything is wacky but adjclose is in the same order of
        # magnitude as the secondary historic rate so return adjclose
        indicators = {
            "adjclose": [{"adjclose": [3270]}],
            "quote": [
                {
                    "close": [3270],
                    "high": [33333.200],
                    "low": [3.999938964844],
                    "open": [33.199951171875],
                    "volume": [0],
                }
            ],
        }
        timestamp = get_int_timestamp(parse_date("2015-12-15"))
        assert Currency._get_adjclose(indicators, "COP", timestamp) == 3270

        Currency._no_historic = True
        assert Currency._get_adjclose(indicators, "COP", timestamp) is None
