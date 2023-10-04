[![Build Status](https://github.com/OCHA-DAP/hdx-python-country/actions/workflows/run-python-tests.yaml/badge.svg)](https://github.com/OCHA-DAP/hdx-python-country/actions/workflows/run-python-tests.yaml)
[![Coverage Status](https://coveralls.io/repos/github/OCHA-DAP/hdx-python-country/badge.svg?branch=main&ts=1)](https://coveralls.io/github/OCHA-DAP/hdx-python-country?branch=main)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![Downloads](https://img.shields.io/pypi/dm/hdx-python-country.svg)](https://pypistats.org/packages/hdx-python-country)

The HDX Python Country Library provides utilities to map between country and region
codes and names and to match administrative level names from different sources.
It also provides utilities for foreign exchange enabling obtaining current and historic
FX rates for different currencies.

It provides country mappings including ISO 2 and ISO 3 letter codes (ISO 3166) and regions
using live official data from the [UN OCHA](https://vocabulary.unocha.org/) feed with
fallbacks to an internal static file if there is any problem with retrieving data from
the url. (Also it is possible to force the use of the internal static files.)

It can exact match English, French, Spanish, Russian, Chinese and Arabic. There is a
fuzzy matching for English look up that can handle abbreviations in country names like
Dem. for Democratic and Rep. for Republic.

Mapping administration level names from a source to a given base set is also handled
including phonetic fuzzy name matching.

It also provides foreign exchange rates and conversion from amounts in local currency to
USD and vice-versa. The conversion relies on Yahoo Finance, falling back on
[currency-api](https://github.com/fawazahmed0/currency-api) for current rates,
and Yahoo Finance falling back on IMF data via IATI for historic rates.

For more information, please read the [documentation](https://hdx-python-country.readthedocs.io/en/latest/).

This library is part of the [Humanitarian Data Exchange](https://data.humdata.org/)
(HDX) project. If you have humanitarian related data, please upload your datasets to
HDX.
