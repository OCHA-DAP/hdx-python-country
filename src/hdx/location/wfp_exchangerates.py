import logging
from typing import Dict, List

from . import get_int_timestamp
from .wfp_api import WFPAPI
from hdx.utilities.dateparse import parse_date
from hdx.utilities.downloader import Download
from hdx.utilities.retriever import Retrieve
from hdx.utilities.typehint import ListTuple

logger = logging.getLogger(__name__)


class WFPExchangeRates:
    """Obtain WFP official exchange rates. It needs a token_downloader that has
    been configured with WFP basic authentication credentials and a retriever
    that will configured by this class with the bearer token obtained from the
    token_downloader.

    Args:
        token_downloader (Download): Download object with WFP basic authentication
        retriever (Retrieve): Retrieve object for interacting with WFP API
    """

    def __init__(self, token_downloader: Download, retriever: Retrieve):
        self.wfpapi = WFPAPI(token_downloader, retriever)
        self.wfpapi.update_retry_params(attempts=5, wait=5)

    def get_currencies(self) -> List[str]:
        """Get list of currencies in WFP API

        Returns:
            List[str]: List of currencies in WFP API
        """
        currencies = []
        for currency in self.wfpapi.get_items("Currency/List"):
            currencies.append(currency["name"])
        return currencies

    def get_currency_historic_rates(self, currency: str) -> Dict[int, float]:
        """Get historic rates for currency from WFP API

        Args:
            currency (str): Currency

        Returns:
            Dict[int, float]: Mapping from timestamp to rate
        """
        quotes = self.wfpapi.get_items(
            "Currency/UsdIndirectQuotation",
            parameters={"currencyName": currency},
        )
        historic_rates = {}
        for quote in quotes:
            if not quote["isOfficial"]:
                continue
            date = parse_date(quote["date"])
            timestamp = get_int_timestamp(date)
            historic_rates[timestamp] = quote["value"]
        return historic_rates

    def get_historic_rates(
        self, currencies: ListTuple[str]
    ) -> Dict[str, Dict]:
        """Get historic rates for a list of currencies from WFP API

        Args:
            currencies (List[str]): List of currencies

        Returns:
            Dict[str, Dict]: Mapping from currency to mapping from timestamp to rate
        """
        historic_rates = {}
        for currency in currencies:
            logger.info(f"Getting WFP historic rates for {currency}")
            currency_historic_rates = self.get_currency_historic_rates(
                currency
            )
            historic_rates[currency.upper()] = currency_historic_rates
        return historic_rates
