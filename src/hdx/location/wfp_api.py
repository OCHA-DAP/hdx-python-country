import logging
from collections.abc import Callable
from os import getenv
from typing import Any

from data_bridges_client import (
    ApiClient,
    ApiException,
    CommoditiesApi,
    Configuration,
    CurrencyApi,
    MarketPricesApi,
    MarketsApi,
    PagedCommodityListDTO,
    PagedCurrencyListDTO,
    PagedMarketListDTO,
    UsdIndirectQuotationPagedResult,
    ViewExtendedMonthlyAggregatedPricePagedResult,
)
from data_bridges_client.models.commodity_dto import CommodityDTO
from data_bridges_client.models.currency_dto import CurrencyDTO
from data_bridges_client.models.market_dto import MarketDTO
from data_bridges_client.models.usd_indirect_quotation import UsdIndirectQuotation
from data_bridges_client.models.view_extended_monthly_aggregated_price import (
    ViewExtendedMonthlyAggregatedPrice,
)
from data_bridges_client.token import WfpApiToken
from hdx.utilities.loader import load_json
from hdx.utilities.retriever import Retrieve
from hdx.utilities.saver import save_json
from tenacity import (
    Retrying,
    after_log,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
)

logger = logging.getLogger(__name__)


class WFPAPI:
    """Light wrapper around WFP's data-bridges-client library. It needs a
    retriever used only to decide whether to load from disk or hit the
    network and whether to persist the network result. Token refreshing is
    delegated to data_bridges_client's own WfpApiToken.

    Args:
        retriever: Retrieve object for interacting with WFP API
    """

    default_retry_params = {
        "retry": retry_if_exception_type(ApiException),
        "after": after_log(logger, logging.INFO),
    }

    def __init__(
        self,
        retriever: Retrieve,
        wfp_key: str | None = None,
        wfp_secret: str | None = None,
    ):
        self.retriever = retriever
        self.retry_params = {"attempts": 1, "wait": 1}
        if wfp_key:
            self._wfp_key = wfp_key
        else:
            self._wfp_key = getenv("WFP_KEY")
        if wfp_secret:
            self._wfp_secret = wfp_secret
        else:
            self._wfp_secret = getenv("WFP_SECRET")
        self.token = WfpApiToken(api_key=self._wfp_key, api_secret=self._wfp_secret)
        self.configuration = Configuration()
        self.api_client = ApiClient(self.configuration)
        self.currency_api = CurrencyApi(self.api_client)
        self.markets_api = MarketsApi(self.api_client)
        self.commodities_api = CommoditiesApi(self.api_client)
        self.market_prices_api = MarketPricesApi(self.api_client)

    def get_retry_params(self) -> dict:
        return self.retry_params

    def update_retry_params(self, attempts: int, wait: int) -> dict:
        self.retry_params["attempts"] = attempts
        self.retry_params["wait"] = wait
        return self.retry_params

    def refresh_token(self) -> None:
        self.configuration.access_token = self.token.refresh()

    def _with_retry(self, api_method: Callable, **kwargs: Any) -> Any:
        retryer = Retrying(
            retry=self.default_retry_params["retry"],
            after=self.default_retry_params["after"],
            stop=stop_after_attempt(self.retry_params["attempts"]),
            wait=wait_fixed(self.retry_params["wait"]),
        )
        for attempt in retryer:
            with attempt:
                try:
                    return api_method(**kwargs)
                except ApiException as err:
                    if err.status not in (104, 401, 403):
                        raise
                    self.refresh_token()
                    return api_method(**kwargs)

    def _call(
        self,
        api_method: Callable,
        model_cls: type,
        filename: str,
        log: str,
        **kwargs: Any,
    ) -> Any:
        """Call a data_bridges_client API method, loading from or saving to
        disk exactly as Retrieve does, so existing fixtures keep working
        unchanged.

        Args:
            api_method: Bound method on one of the data_bridges_client APIs
            model_cls: Paged result model class to (de)serialize with
            filename: Filename of saved file
            log: Text to use in log string to describe the call
            **kwargs: Parameters to pass to api_method

        Returns:
            An instance of model_cls, or None if there is no saved data
        """
        filename, _ = self.retriever.get_filename("", filename)
        saved_path = self.retriever.saved_dir / filename
        if self.retriever.use_saved:
            logger.info(f"Using saved {log} in {saved_path}")
            try:
                return model_cls.from_dict(load_json(saved_path))
            except FileNotFoundError:
                return None
        result = self._with_retry(api_method, **kwargs)
        if self.retriever.save:
            logger.info(f"Saving {log} in {saved_path}")
            save_json(result.to_dict(), saved_path)
        return result

    @staticmethod
    def _countryiso3s(countryiso3: str | None) -> list:
        if countryiso3 == "PSE":  # hack as PSE is treated by WFP as 2 areas
            return ["PSW", "PSG"]
        return [countryiso3]

    @staticmethod
    def _filename_and_log(
        base_filename: str, countryiso3: str | None, page: int
    ) -> tuple[str, str]:
        if countryiso3 is None:
            return f"{base_filename}_{page}.json", f"{base_filename} page {page}"
        return (
            f"{base_filename}_{countryiso3}_{page}.json",
            f"{base_filename} for {countryiso3} page {page}",
        )

    def _get_all_pages(
        self,
        api_method: Callable,
        model_cls: type,
        base_filename: str,
        countryiso3: str | None,
        country_param: str,
        extra_params: dict,
    ) -> list:
        all_items = []
        for country in self._countryiso3s(countryiso3):
            page = 1
            while True:
                kwargs = dict(extra_params)
                kwargs["page"] = page
                if country is not None:
                    kwargs[country_param] = country
                filename, log = self._filename_and_log(base_filename, country, page)
                result = self._call(api_method, model_cls, filename, log, **kwargs)
                items = result.items if result else None
                if not items:
                    break
                all_items.extend(items)
                page += 1
        return all_items

    def get_currencies(
        self, countryiso3: str | None = None, currency: str | None = None
    ) -> list[CurrencyDTO]:
        """Get list of currencies from the WFP API.

        Args:
            countryiso3: Country for which to obtain data. Defaults to all countries.
            currency: Currency 3-letter code to filter by. Defaults to all currencies.

        Returns:
            List of currencies from the WFP API
        """
        extra_params = {"currency_name": currency} if currency else {}
        return self._get_all_pages(
            self.currency_api.currency_list_get,
            PagedCurrencyListDTO,
            "Currency_List",
            countryiso3,
            "country_code",
            extra_params,
        )

    def get_currency_usd_indirect_quotations(
        self, currency: str, countryiso3: str | None = None
    ) -> list[UsdIndirectQuotation]:
        """Get USD indirect quotations for a currency from the WFP API.

        Args:
            currency: Currency 3-letter code
            countryiso3: Country for which to obtain data. Defaults to all countries.

        Returns:
            List of USD indirect quotations from the WFP API
        """
        return self._get_all_pages(
            self.currency_api.currency_usd_indirect_quotation_get,
            UsdIndirectQuotationPagedResult,
            "Currency_UsdIndirectQuotation",
            countryiso3,
            # this endpoint uses country_iso3, unlike every other one here which
            # uses country_code - don't "fix" this to country_code
            "country_iso3",
            {"currency_name": currency},
        )

    def get_markets(self, countryiso3: str | None = None) -> list[MarketDTO]:
        """Get list of markets from the WFP API.

        Args:
            countryiso3: Country for which to obtain data. Defaults to all countries.

        Returns:
            List of markets from the WFP API
        """
        return self._get_all_pages(
            self.markets_api.markets_list_get,
            PagedMarketListDTO,
            "Markets_List",
            countryiso3,
            "country_code",
            {},
        )

    def get_commodities(self, countryiso3: str | None = None) -> list[CommodityDTO]:
        """Get list of commodities from the WFP API.

        Args:
            countryiso3: Country for which to obtain data. Defaults to all countries.

        Returns:
            List of commodities from the WFP API
        """
        return self._get_all_pages(
            self.commodities_api.commodities_list_get,
            PagedCommodityListDTO,
            "Commodities_List",
            countryiso3,
            "country_code",
            {},
        )

    def get_commodity_categories(
        self, countryiso3: str | None = None
    ) -> list[CommodityDTO]:
        """Get list of commodity categories from the WFP API.

        Args:
            countryiso3: Country for which to obtain data. Defaults to all countries.

        Returns:
            List of commodity categories from the WFP API
        """
        return self._get_all_pages(
            self.commodities_api.commodities_categories_list_get,
            PagedCommodityListDTO,
            "Commodities_Categories_List",
            countryiso3,
            "country_code",
            {},
        )

    def get_market_prices_monthly(
        self, countryiso3: str | None = None, **kwargs: Any
    ) -> list[ViewExtendedMonthlyAggregatedPrice]:
        """Get monthly aggregated market prices from the WFP API.

        Args:
            countryiso3: Country for which to obtain data. Defaults to all countries.
            **kwargs: Additional filters accepted by
                data_bridges_client's MarketPricesApi.market_prices_price_monthly_get,
                e.g. market_id, commodity_id, price_type_name, currency_id,
                price_flag, start_date, end_date, latest_value_only

        Returns:
            List of monthly aggregated market prices from the WFP API
        """
        return self._get_all_pages(
            self.market_prices_api.market_prices_price_monthly_get,
            ViewExtendedMonthlyAggregatedPricePagedResult,
            "MarketPrices_PriceMonthly",
            countryiso3,
            "country_code",
            kwargs,
        )
