from os.path import join

import pytest

from hdx.location.currency import Currency


@pytest.fixture(scope="session")
def fixtures_dir():
    return join("tests", "fixtures")


@pytest.fixture(scope="session")
def input_dir(fixtures_dir):
    return join(fixtures_dir, "wfp")


@pytest.fixture(scope="function")
def reset_currency():
    Currency._cached_current_rates = {}
    Currency._cached_historic_rates = {}
    Currency._rates_api = ""
    Currency._secondary_rates = {}
    Currency._secondary_historic_rates = {}
    Currency._fallback_to_current = False
    Currency._no_historic = False
