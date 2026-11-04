import csv
import logging
import types
from collections.abc import Callable
from datetime import date, datetime, timedelta
from functools import cache, partial
from os import getenv
from typing import Annotated, Any, ClassVar, Union, get_args, get_origin

from data_bridges_client import (
    ApiClient,
    ApiException,
    CommoditiesApi,
    Configuration,
    CurrencyApi,
    MarketPricesApi,
    MarketsApi,
)
from data_bridges_client.exceptions import ServiceException
from data_bridges_client.models.commodity_dto import CommodityDTO
from data_bridges_client.models.currency_dto import CurrencyDTO
from data_bridges_client.models.market_dto import MarketDTO
from data_bridges_client.models.usd_indirect_quotation import UsdIndirectQuotation
from data_bridges_client.models.view_extended_monthly_aggregated_price import (
    ViewExtendedMonthlyAggregatedPrice,
)
from data_bridges_client.token import WfpApiToken
from hdx.utilities.retriever import Retrieve
from tenacity import (
    Retrying,
    after_log,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
)

logger = logging.getLogger(__name__)

_CSV_DATE_FORMAT = "%m/%d/%Y %I:%M:%S %p"
_PRICES_START_DATE = date(1990, 1, 1)


def _default_end_date() -> date:
    # WFP has forecast prices a year or more ahead
    return date(date.today().year + 5, 12, 31)


def _to_date(value: date | None, default: date) -> date:
    if value is None:
        return default
    if isinstance(value, datetime):
        return value.date()
    return value


def _csv_datetime(value: str) -> datetime:
    return datetime.strptime(value, _CSV_DATE_FORMAT)


def _csv_bool(value: str) -> bool:
    return value == "True"


def _csv_none(value: str) -> None:
    return None


def _field_types(annotation: Any) -> set:
    origin = get_origin(annotation)
    if origin is Annotated:
        return _field_types(get_args(annotation)[0])
    if origin in (Union, types.UnionType):
        return set().union(
            *(_field_types(x) for x in get_args(annotation) if x is not type(None))
        )
    return {origin or annotation}


@cache
def _csv_converters(model_cls: type) -> dict[str, Callable]:
    """Map the JSON key of each non-string field of a data_bridges_client
    model to a function that converts its CSV string value, based on the
    field's type. List fields (CommodityDTO's qualities and processing) are
    not in WFP's CSV output, so are always None.

    Args:
        model_cls: data_bridges_client model class

    Returns:
        Map from JSON key to converter function
    """
    converters = {}
    for name, field in model_cls.model_fields.items():
        if name == "additional_properties":
            continue
        field_types = _field_types(field.annotation)
        if list in field_types:
            converter = _csv_none
        elif bool in field_types:
            converter = _csv_bool
        elif float in field_types:
            converter = float
        elif int in field_types:
            converter = int
        elif datetime in field_types:
            converter = _csv_datetime
        else:
            continue
        converters[field.alias or name] = converter
    return converters


def _parse_csv(text: str, model_cls: type) -> list:
    """Parse WFP's CSV output into data_bridges_client model objects. CSV
    headers are the JSON keys with the first letter capitalised and every
    value is a string. Blank strings are kept as "" (as JSON returns them)
    but blank values of non-string fields become None. Values and pydantic
    fields sets are shared between rows to limit memory use (see
    docs/decisions/0003).

    Args:
        text: CSV text
        model_cls: data_bridges_client model class of each row

    Returns:
        List of model_cls objects
    """
    converters = _csv_converters(model_cls)
    reader = csv.reader(f"{line}\n" for line in text.split("\n"))
    keys = [header[0].lower() + header[1:] for header in next(reader, [])]
    columns = [(key, converters.get(key), {}) for key in keys]
    fields_sets = {}
    items = []
    for row in reader:
        if not row:
            continue
        obj = {}
        for (key, converter, values), value in zip(columns, row):
            try:
                obj[key] = values[value]
            except KeyError:
                if converter:
                    converted = converter(value) if value else None
                else:
                    converted = value
                values[value] = converted
                obj[key] = converted
        item = model_cls.from_dict(obj)
        fields_set = frozenset(item.__pydantic_fields_set__)
        fields_set = fields_sets.setdefault(fields_set, item.__pydantic_fields_set__)
        object.__setattr__(item, "__pydantic_fields_set__", fields_set)
        items.append(item)
    return items


class WFPAPI:
    """Light wrapper around WFP's data-bridges-client library. All data is
    requested as CSV (see docs/decisions/0001). It needs a retriever used
    only to decide whether to load from disk or hit the network and whether
    to persist the network result (as the CSV returned by WFP). Token
    refreshing is delegated to data_bridges_client's own WfpApiToken.

    Args:
        retriever: Retrieve object for interacting with WFP API
    """

    default_retry_params: ClassVar[dict[str, Any]] = {
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

    @staticmethod
    def _get_csv(api_method: Callable, **kwargs: Any) -> str:
        """Call a data_bridges_client API method's _without_preload_content
        variant with format CSV, raising ApiException (as the methods that
        parse JSON do) if the response is not OK.

        Args:
            api_method: Bound _without_preload_content method
            **kwargs: Parameters to pass to api_method

        Returns:
            CSV text
        """
        response = api_method(format="CSV", **kwargs)
        text = response.data.decode("utf-8-sig")
        if response.status != 200:
            ApiException.from_response(http_resp=response, body=text, data=None)
        return text

    def _call(
        self, csv_method: Callable, filename: str, log: str, **kwargs: Any
    ) -> str | None:
        """Get CSV text from csv_method, loading from or saving to disk as
        Retrieve does.

        Args:
            csv_method: Function returning CSV text
            filename: Filename of saved file
            log: Text to use in log string to describe the call
            **kwargs: Parameters to pass to csv_method

        Returns:
            CSV text, or None if there is no saved data
        """
        filename, _ = self.retriever.get_filename("", filename)
        saved_path = self.retriever.saved_dir / filename
        if self.retriever.use_saved:
            logger.info(f"Using saved {log} in {saved_path}")
            try:
                with open(saved_path, encoding="utf-8", newline="") as f:
                    return f.read()
            except FileNotFoundError:
                return None
        text = self._with_retry(csv_method, **kwargs)
        if self.retriever.save:
            logger.info(f"Saving {log} in {saved_path}")
            with open(saved_path, "w", encoding="utf-8", newline="") as f:
                f.write(text)
        return text

    @staticmethod
    def _countryiso3s(countryiso3: str | None) -> list:
        if countryiso3 == "PSE":  # see docs/decisions/0004
            return ["PSW", "PSG"]
        return [countryiso3]

    def _get_all(
        self,
        api_method: Callable,
        model_cls: type,
        base_filename: str,
        countryiso3: str | None,
        country_param: str,
        extra_params: dict,
        get_csv: Callable | None = None,
    ) -> list:
        csv_method = partial(get_csv or self._get_csv, api_method)
        all_items = []
        for country in self._countryiso3s(countryiso3):
            kwargs = dict(extra_params)
            if country is None:
                filename = f"{base_filename}.csv"
                log = base_filename
            else:
                kwargs[country_param] = country
                filename = f"{base_filename}_{country}.csv"
                log = f"{base_filename} for {country}"
            text = self._call(csv_method, filename, log, **kwargs)
            if text:
                all_items.extend(_parse_csv(text, model_cls))
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
        if currency:
            base_filename = f"Currency_List_{currency.upper()}"
            extra_params = {"currency_name": currency}
        else:
            base_filename = "Currency_List"
            extra_params = {}
        return self._get_all(
            self.currency_api.currency_list_get_without_preload_content,
            CurrencyDTO,
            base_filename,
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
        return self._get_all(
            self.currency_api.currency_usd_indirect_quotation_get_without_preload_content,
            UsdIndirectQuotation,
            f"Currency_UsdIndirectQuotation_{currency.upper()}",
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
        return self._get_all(
            self.markets_api.markets_list_get_without_preload_content,
            MarketDTO,
            "Markets_List",
            countryiso3,
            "country_code",
            {},
        )

    def get_commodities(self, countryiso3: str | None = None) -> list[CommodityDTO]:
        """Get list of commodities from the WFP API. WFP's CSV output does not
        include qualities and processing, so they are None.

        Args:
            countryiso3: Country for which to obtain data. Defaults to all countries.

        Returns:
            List of commodities from the WFP API
        """
        return self._get_all(
            self.commodities_api.commodities_list_get_without_preload_content,
            CommodityDTO,
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
        return self._get_all(
            self.commodities_api.commodities_categories_list_get_without_preload_content,
            CommodityDTO,
            "Commodities_Categories_List",
            countryiso3,
            "country_code",
            {},
        )

    def _get_prices_csv_range(
        self, api_method: Callable, start_date: date, end_date: date, **kwargs: Any
    ) -> list[str]:
        """Get monthly aggregated market prices between two dates (inclusive)
        as CSV. If the API gateway times out (504), the date range is split in
        two and each half is requested (see docs/decisions/0002).

        Args:
            api_method: Bound market_prices_price_monthly_get_without_preload_content
            start_date: Start date
            end_date: End date
            **kwargs: Parameters to pass to api_method

        Returns:
            List of CSV texts, one per date range, in date order
        """
        try:
            return [
                self._get_csv(
                    api_method, start_date=start_date, end_date=end_date, **kwargs
                )
            ]
        except ServiceException as err:
            if err.status != 504 or start_date >= end_date:
                raise
        middle = start_date + (end_date - start_date) // 2
        logger.info(
            f"Timeout getting prices from {start_date} to {end_date}, splitting at {middle}"
        )
        return self._get_prices_csv_range(
            api_method, start_date, middle, **kwargs
        ) + self._get_prices_csv_range(
            api_method, middle + timedelta(days=1), end_date, **kwargs
        )

    def _get_prices_csv(
        self,
        api_method: Callable,
        start_date: date | None = None,
        end_date: date | None = None,
        **kwargs: Any,
    ) -> str:
        first, *rest = self._get_prices_csv_range(
            api_method,
            _to_date(start_date, _PRICES_START_DATE),
            _to_date(end_date, _default_end_date()),
            **kwargs,
        )
        if not rest:
            return first
        # keep only the first range's header row
        parts = [first.rstrip("\r\n")]
        parts.extend(text.partition("\n")[2].rstrip("\r\n") for text in rest)
        return "\r\n".join(part for part in parts if part) + "\r\n"

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
        return self._get_all(
            self.market_prices_api.market_prices_price_monthly_get_without_preload_content,
            ViewExtendedMonthlyAggregatedPrice,
            "MarketPrices_PriceMonthly",
            countryiso3,
            "country_code",
            kwargs,
            self._get_prices_csv,
        )
