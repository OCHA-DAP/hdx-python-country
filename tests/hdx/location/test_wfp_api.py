from datetime import date, datetime, timedelta
from itertools import pairwise

import pytest
from data_bridges_client import ApiException
from data_bridges_client.models.view_extended_monthly_aggregated_price import (
    ViewExtendedMonthlyAggregatedPrice,
)
from hdx.utilities.downloader import Download
from hdx.utilities.path import temp_dir
from hdx.utilities.retriever import Retrieve
from tenacity import RetryError

from hdx.location.wfp_api import (
    _PRICES_START_DATE,
    WFPAPI,
    _default_end_date,
    _parse_csv,
)


class StubResponse:
    def __init__(self, status: int, data: bytes):
        self.status = status
        self.reason = "Stub"
        self.data = data
        self.headers = {}


def ok(text):
    return lambda **kwargs: StubResponse(200, text.encode("utf-8"))


@pytest.fixture(scope="module")
def prices_csv(input_dir):
    with open(input_dir / "MarketPrices_PriceMonthly_BTN.csv", encoding="utf-8") as f:
        return f.read()


class TestWFPAPI:
    @staticmethod
    def get_wfp_api(tempdir, save=False, use_saved=False):
        retriever = Retrieve(
            Download(user_agent="test"),
            tempdir,
            tempdir,
            tempdir,
            save=save,
            use_saved=use_saved,
        )
        return WFPAPI(retriever)

    @staticmethod
    def stub_api(api, method_name, monkeypatch, response):
        calls = []

        def get_csv(**kwargs):
            calls.append(kwargs)
            return response(**kwargs)

        monkeypatch.setattr(api, f"{method_name}_without_preload_content", get_csv)
        return calls

    def stub_prices(self, wfp_api, monkeypatch, response):
        return self.stub_api(
            wfp_api.market_prices_api,
            "market_prices_price_monthly_get",
            monkeypatch,
            response,
        )

    def test_parse_prices_csv(self, prices_csv):
        prices = _parse_csv(prices_csv, ViewExtendedMonthlyAggregatedPrice)
        assert len(prices) == 4
        price = prices[0]
        assert price.commodity_id == 58
        assert price.market_id == 1036
        assert price.commodity_date_week is None
        assert price.commodity_date_month == 3
        assert price.commodity_price_date == datetime(2006, 3, 15)
        assert price.commodity_price == 12.55
        assert price.commodity_price_observations == 1
        assert price.commodity_price_source_name == "National Statistics Bureau"
        assert price.country_iso3 == "BTN"
        assert price.additional_properties == {}
        price = prices[2]
        assert price.commodity_price_source_name == ""
        assert price.commodity_price_observations is None
        assert price.commodity_price_flag == "forecast"
        assert prices[3].commodity_price_date == datetime(2006, 12, 15)

    def test_get_market_prices_monthly(self, prices_csv, monkeypatch):
        with temp_dir("TestWFPAPI", delete_on_failure=False) as tempdir:
            wfp_api = self.get_wfp_api(tempdir)
            calls = self.stub_prices(
                wfp_api,
                monkeypatch,
                ok(prices_csv),
            )
            prices = wfp_api.get_market_prices_monthly(countryiso3="BTN")
            assert len(prices) == 4
            assert calls == [
                {
                    "start_date": _PRICES_START_DATE,
                    "end_date": _default_end_date(),
                    "format": "CSV",
                    "country_code": "BTN",
                }
            ]

            calls.clear()
            prices = wfp_api.get_market_prices_monthly(
                countryiso3="PSE",
                start_date=datetime(2020, 1, 1),
                end_date=date(2020, 12, 31),
            )
            assert len(prices) == 8
            assert [x["country_code"] for x in calls] == ["PSW", "PSG"]
            assert calls[0]["start_date"] == date(2020, 1, 1)
            assert calls[0]["end_date"] == date(2020, 12, 31)

    def test_get_market_prices_monthly_error(self, monkeypatch):
        with temp_dir("TestWFPAPI", delete_on_failure=False) as tempdir:
            wfp_api = self.get_wfp_api(tempdir)
            self.stub_prices(
                wfp_api, monkeypatch, lambda **kwargs: StubResponse(500, b"Error")
            )
            with pytest.raises(RetryError) as excinfo:
                wfp_api.get_market_prices_monthly(countryiso3="BTN")
            exception = excinfo.value.last_attempt.exception()
            assert isinstance(exception, ApiException)
            assert exception.status == 500

    def test_get_market_prices_monthly_split(self, prices_csv, monkeypatch):
        header, *rows = prices_csv.splitlines()
        row_dates = [
            x.commodity_price_date.date()
            for x in _parse_csv(prices_csv, ViewExtendedMonthlyAggregatedPrice)
        ]

        def response(start_date, end_date, **kwargs):
            if (end_date - start_date).days > 2000:
                return StubResponse(504, b"Gateway Timeout")
            lines = [header] + [
                row
                for row, row_date in zip(rows, row_dates)
                if start_date <= row_date <= end_date
            ]
            return StubResponse(200, "\n".join(lines).encode("utf-8"))

        with temp_dir("TestWFPAPI", delete_on_failure=False) as tempdir:
            wfp_api = self.get_wfp_api(tempdir)
            calls = self.stub_prices(wfp_api, monkeypatch, response)
            prices = wfp_api.get_market_prices_monthly(countryiso3="BTN")
            assert sorted(x.commodity_price_date.date() for x in prices) == sorted(
                row_dates
            )
            ranges = [
                (x["start_date"], x["end_date"])
                for x in calls
                if (x["end_date"] - x["start_date"]).days <= 2000
            ]
            assert len(ranges) > 1
            assert ranges[0][0] == _PRICES_START_DATE
            assert ranges[-1][1] == _default_end_date()
            for (_, end), (start, _) in pairwise(ranges):
                assert start == end + timedelta(days=1)

    def test_get_market_prices_monthly_saved(self, prices_csv, monkeypatch):
        with temp_dir("TestWFPAPI", delete_on_failure=False) as tempdir:
            wfp_api = self.get_wfp_api(tempdir, save=True)
            self.stub_prices(
                wfp_api,
                monkeypatch,
                ok(prices_csv),
            )
            prices = wfp_api.get_market_prices_monthly(countryiso3="BTN")
            wfp_api = self.get_wfp_api(tempdir, use_saved=True)
            saved_prices = wfp_api.get_market_prices_monthly(countryiso3="BTN")
            assert saved_prices == prices

    def test_get_currency_usd_indirect_quotations(self, input_dir, monkeypatch):
        with open(
            input_dir / "Currency_UsdIndirectQuotation_SYP.csv", encoding="utf-8"
        ) as f:
            quotations_csv = f.read()
        with temp_dir("TestWFPAPI", delete_on_failure=False) as tempdir:
            wfp_api = self.get_wfp_api(tempdir, save=True)
            calls = self.stub_api(
                wfp_api.currency_api,
                "currency_usd_indirect_quotation_get",
                monkeypatch,
                ok(quotations_csv),
            )
            quotations = wfp_api.get_currency_usd_indirect_quotations("SYP")
            assert calls == [{"currency_name": "SYP", "format": "CSV"}]
            assert [x.to_dict() for x in quotations] == [
                {
                    "id": 78,
                    "name": "SYP",
                    "adm0Code": 238,
                    "countryISO3": "SYR",
                    "isOfficial": True,
                    "frequency": "Daily",
                    "value": 122.0,
                    "date": datetime(2026, 11, 2),
                },
                {
                    "id": 78,
                    "name": "SYP",
                    "adm0Code": 238,
                    "countryISO3": "SYR",
                    "isOfficial": False,
                    "frequency": "Monthly",
                    "value": 11773.0,
                    "date": datetime(2026, 12, 15),
                },
                {
                    "id": 78,
                    "name": "SYP",
                    "adm0Code": 238,
                    "countryISO3": "SYR",
                    "isOfficial": False,
                    "frequency": "Weekly",
                    "value": 137.56,
                    "date": datetime(2026, 9, 21),
                },
            ]
            wfp_api = self.get_wfp_api(tempdir, use_saved=True)
            assert wfp_api.get_currency_usd_indirect_quotations("SYP") == quotations
