import logging
from typing import Dict, List

from .int_timestamp import get_int_timestamp
from .wfp_api import WFPAPI
from hdx.utilities.dateparse import parse_date
from hdx.utilities.typehint import ListTuple

logger = logging.getLogger(__name__)


class WFPExchangeRates:
    """Obtain WFP official exchange rates. It needs a WFP API object.

    Args:
        wfp_api (WFPAPI): WFPAPI object
    """

    def __init__(self, wfp_api: WFPAPI):
        self.wfp_api = wfp_api

    def get_currencies_info(self) -> List[Dict]:
        """Get list of currency codes and names from WFP API

        Returns:
            List[Dict]: List of currency codes and names in WFP API
        """
        currencies = []
        for currency in self.wfp_api.get_items("Currency/List"):
            currency_name = currency["extendedName"]
            if currency_name:
                currency_name = currency_name.strip()
            currencies.append({"code": currency["name"], "name": currency_name})
        return currencies

    def get_currencies(self) -> List[str]:
        """Get list of currency codes in WFP API

        Returns:
            List[str]: List of currency codes in WFP API
        """
        currencies = []
        for currency in self.wfp_api.get_items("Currency/List"):
            currencies.append(currency["name"])
        return currencies

    def get_currency_historic_rates(self, currency: str) -> Dict[int, float]:
        """Get historic rates for currency from WFP API

        Args:
            currency (str): Currency

        Returns:
            Dict[int, float]: Mapping from timestamp to rate
        """
        quotes = self.wfp_api.get_items(
            "Currency/UsdIndirectQuotation",
            parameters={"currencyName": currency},
        )
        historic_rates = {}
        for quote in reversed(quotes):
            if not quote["isOfficial"]:
                continue
            date = parse_date(quote["date"])
            timestamp = get_int_timestamp(date)
            historic_rates[timestamp] = quote["value"]
        return historic_rates

    def get_historic_rates(self, currencies: ListTuple[str]) -> Dict[str, Dict]:
        """Get historic rates for a list of currencies from WFP API

        Args:
            currencies (List[str]): List of currencies

        Returns:
            Dict[str, Dict]: Mapping from currency to mapping from timestamp to rate
        """
        historic_rates = {}
        for currency in currencies:
            logger.info(f"Getting WFP historic rates for {currency}")
            currency_historic_rates = self.get_currency_historic_rates(currency)
            historic_rates[currency.upper()] = currency_historic_rates
        return historic_rates
