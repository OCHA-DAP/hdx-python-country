import logging
from datetime import timezone
from typing import Dict, List

from . import get_int_timestamp
from hdx.utilities.typehint import ListTuple

try:
    from data_bridges_client import ApiClient, CurrencyApi
    from data_bridges_client.exceptions import ApiException
    from data_bridges_client.token import WfpApiToken
except ImportError:
    WfpApiToken = None

logger = logging.getLogger(__name__)


class WFPExchangeRates:
    """Obtain WFP official exchange rates. Requires WFP credentials amd
    installation of the WFP extra eg. `pip install hdx-python-country[wfp]`

    Args:
        key: WFP API key
        secret: WFP API secret
    """

    def __init__(self, key: str, secret: str):
        # Configure OAuth2 access token for authorization: default
        self.token = WfpApiToken(api_key=key, api_secret=secret)
        self.configuration = self.token.refresh_configuration()
        api_client = ApiClient(self.configuration)
        self.api_instance = CurrencyApi(api_client)

    def get_currencies(self) -> List[str]:
        """Get list of currencies in WFP API

        Returns:
            List[str]: List of currencies in WFP API
        """
        currencies = []
        for currencydto in self.api_instance.currency_list_get().items:
            currencies.append(currencydto.name)
        return currencies

    def get_currency_historic_rates(self, currency: str) -> Dict[int, float]:
        """Get historic rates for currency from WFP API

        Args:
            currency (str): Currency

        Returns:
            Dict[int, float]: Mapping from timestamp to rate
        """
        historic_rates = {}
        page = 1
        while True:
            try:
                usdquotations = (
                    self.api_instance.currency_usd_indirect_quotation_get(
                        currency_name=currency, page=page
                    ).items
                )
            except ApiException as ex:
                if ex.status not in (104, 401, 403):
                    raise
                self.configuration.access_token = self.token.refresh()
                usdquotations = (
                    self.api_instance.currency_usd_indirect_quotation_get(
                        currency_name=currency, page=page
                    ).items
                )
            if not usdquotations:
                break
            for usdquotation in usdquotations:
                if not usdquotation.is_official:
                    continue
                date = usdquotation.var_date.replace(tzinfo=timezone.utc)
                timestamp = get_int_timestamp(date)
                historic_rates[timestamp] = usdquotation.value
            page = page + 1
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
