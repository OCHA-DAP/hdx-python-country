import logging
from typing import Any, Dict, List, Optional

from tenacity import (
    Retrying,
    after_log,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
)

from hdx.utilities.base_downloader import DownloadError
from hdx.utilities.downloader import Download
from hdx.utilities.retriever import Retrieve

logger = logging.getLogger(__name__)


class WFPAPI:
    """Light wrapper around WFP REST API. It needs a token_downloader that has
    been configured with WFP basic authentication credentials and a retriever
    that will configured by this class with the bearer token obtained from the
    token_downloader.

    Args:
        token_downloader (Download): Download object with WFP basic authentication
        retriever (Retrieve): Retrieve object for interacting with WFP API
    """

    token_url = "https://api.wfp.org/token"
    base_url = "https://api.wfp.org/vam-data-bridges/5.0.0/"
    scope = "vamdatabridges_commodities-list_get vamdatabridges_commodityunits-list_get vamdatabridges_marketprices-alps_get vamdatabridges_commodities-categories-list_get vamdatabridges_commodityunits-conversion-list_get vamdatabridges_marketprices-priceweekly_get vamdatabridges_markets-geojsonlist_get vamdatabridges_marketprices-pricemonthly_get vamdatabridges_markets-list_get vamdatabridges_currency-list_get vamdatabridges_currency-usdindirectquotation_get"
    default_retry_params = {
        "retry": retry_if_exception_type(DownloadError),
        "after": after_log(logger, logging.INFO),
    }

    def __init__(
        self,
        token_downloader: Download,
        retriever: Retrieve,
    ):
        self.token_downloader = token_downloader
        self.retriever = retriever
        self.retry_params = {"attempts": 1, "wait": 1}

    def get_retry_params(self) -> Dict:
        return self.retry_params

    def update_retry_params(self, attempts: int, wait: int) -> Dict:
        self.retry_params["attempts"] = attempts
        self.retry_params["wait"] = wait
        return self.retry_params

    def refresh_token(self) -> None:
        self.token_downloader.download(
            self.token_url,
            post=True,
            parameters={
                "grant_type": "client_credentials",
                "scope": self.scope,
            },
        )
        bearer_token = self.token_downloader.get_json()["access_token"]
        self.retriever.downloader.set_bearer_token(bearer_token)

    def retrieve(
        self,
        url: str,
        filename: str,
        log: str,
        parameters: Optional[Dict] = None,
    ) -> Any:
        """Retrieve JSON from WFP API.

        Args:
            url (str): URL to download
            filename (Optional[str]): Filename of saved file. Defaults to getting from url.
            log (Optional[str]): Text to use in log string to describe download. Defaults to filename.
            parameters (Dict): Parameters to pass to download_json call

        Returns:
            Any: The data from the JSON file
        """
        retryer = Retrying(
            retry=self.default_retry_params["retry"],
            after=self.default_retry_params["after"],
            stop=stop_after_attempt(self.retry_params["attempts"]),
            wait=wait_fixed(self.retry_params["wait"]),
        )
        for attempt in retryer:
            with attempt:
                try:
                    results = self.retriever.download_json(
                        url, filename, log, False, parameters=parameters
                    )
                except DownloadError:
                    response = self.retriever.downloader.response
                    if response and response.status_code not in (
                        104,
                        401,
                        403,
                    ):
                        raise
                    self.refresh_token()
                    results = self.retriever.download_json(
                        url, filename, log, False, parameters=parameters
                    )
                return results

    def get_items(
        self,
        endpoint: str,
        countryiso3: Optional[str] = None,
        parameters: Optional[Dict] = None,
    ) -> List:
        """Retrieve a list of items from the WFP API.

        Args:
            endpoint (str): End point to call
            countryiso3 (Optional[str]): Country for which to obtain data. Defaults to all countries.
            parameters (Optional[Dict]): Paramaters to pass to call. Defaults to None.

        Returns:
            List: List of items from the WFP endpoint
        """
        if not parameters:
            parameters = {}
        all_data = []
        url = f"{self.base_url}{endpoint}"
        url_parts = url.split("/")
        base_filename = f"{url_parts[-2]}_{url_parts[-1]}"
        if countryiso3 == "PSE":  # hack as PSE is treated by WFP as 2 areas
            countryiso3s = ["PSW", "PSG"]
        else:
            countryiso3s = [countryiso3]
        for countryiso3 in countryiso3s:
            page = 1
            data = None
            while data is None or len(data) > 0:
                page_parameters = {"page": page}
                page_parameters.update(parameters)
                if countryiso3 is None:
                    filename = f"{base_filename}_{page}.json"
                    log = f"{base_filename} page {page}"
                else:
                    filename = f"{base_filename}_{countryiso3}_{page}.json"
                    log = f"{base_filename} for {countryiso3} page {page}"
                    page_parameters["CountryCode"] = countryiso3
                try:
                    json = self.retrieve(url, filename, log, page_parameters)
                except FileNotFoundError:
                    json = {"items": []}
                data = json["items"]
                all_data.extend(data)
                page = page + 1
        return all_data
