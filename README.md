[![Build Status](https://github.com/OCHA-DAP/hdx-python-country/workflows/build/badge.svg)](https://github.com/OCHA-DAP/hdx-python-country/actions?query=workflow%3Abuild)
[![Coverage Status](https://codecov.io/gh/OCHA-DAP/hdx-python-country/branch/main/graph/badge.svg?token=JpWZc5js4y)](https://codecov.io/gh/OCHA-DAP/hdx-python-country)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)

The HDX Python Country Library provides utilities to map between country and region codes 
and names, to convert between currencies and to match administrative level one names from different sources.  

It provides country mappings including ISO 2 and ISO 3 letter codes (ISO 3166) and regions 
using live official data from the [UN OCHA](https://vocabulary.unocha.org/) feed with fallbacks to an internal static 
file if there is any problem with retrieving data from the url. (Also it is possible to force the use of the internal 
static files.)

It can exact match English, French, Spanish, Russian, Chinese and Arabic. There is a fuzzy matching for English look up 
that can handle abbreviations in country names like Dem. for Democratic and Rep. for Republic.

Mapping administration level one names from a source to a given base set is also handled including phonetic fuzzy name 
matching if you are running Python 3.  

It also provides currency conversion to USD from local currency.

For more information, please read the [documentation](https://hdx-python-country.readthedocs.io/en/latest/). 

This library is part of the [Humanitarian Data Exchange](https://data.humdata.org/) (HDX) project. If you have 
humanitarian related data, please upload your datasets to HDX.
