|Build_Status| |Coverage_Status|

The HDX Python Country Library provides country mappings including ISO 2 and ISO 3
letter codes (ISO 3166) and regions using live official data from the `UNStats M49`_
website and `World Bank`_ api with fallbacks to internal static files if there is any
problem with retrieving data from the urls. (Also it is possible to force the use of
the internal static files.)

There is a fuzzy matching look up that can handle abbreviations in country names like
Dem. for Democratic and Rep. for Republic.

This library is part of the `Humanitarian Data Exchange`_ (HDX) project. If you have
humanitarian related data, please upload your datasets to HDX.

-  `Usage <#usage>`__
-  `Countries <#countries>`__

Usage
-----

The library has detailed API documentation which can be found
here: \ http://ocha-dap.github.io/hdx-python-country/. The code for the
library is here: \ https://github.com/ocha-dap/hdx-python-country.

Countries
~~~~~~~~~

The usage of the country mappings functionality is best illustrated by some examples:

::

    from hdx.location.country import Country

    Country.get_country_name_from_iso3('jpn', use_live=False)  # returns 'Japan'
    # uselive=False forces the use of internal files instead of accessing the live feeds.
    # It only needs to be supplied to the first call as the data once loaded is held
    # in internal dictionaries for future use.
    Country.get_country_name_from_iso2('Pl')  # returns 'Poland'
    Country.get_iso3_country_code('UZBEKISTAN')  # returns 'UZB'

    Country.get_iso3_country_code_fuzzy('Sierra')
    # performs fuzzy match and returns ('SLE', False). The False indicates a fuzzy rather than exact match.
    assert Country.get_iso3_country_code_fuzzy('Czech Rep.')
    # returns ('CZE', False)

    Country.get_country_info_from_iso2('jp')
    # {'Sub-region Name': 'Eastern Asia', 'M49 Code': '392', 'ISO-alpha3 Code': 'JPN',
    'Developed / Developing Countries': 'Developed', 'Land Locked Developing Countries (LLDC)': '',
    'Global Name': 'World', 'Region Name': 'Asia', 'Least Developed Countries (LDC)': '',
    'Intermediate Region Code': '', 'Region Code': '142', 'Country or Area': 'Japan', 'Sub-region Code': '030',
    'Intermediate Region Name': '', 'Small Island Developing States (SIDS)': '', 'Global Code': '001'}

    Country.get_countries_in_region('Channel Islands')
    # ['GGY', 'JEY']
    len(Country.get_countries_in_region('Africa'))
    # 60
    Country.get_countries_in_region('013')
    # ['BLZ', 'CRI', 'GTM', 'HND', 'MEX', 'NIC', 'PAN', 'SLV']


**get_countries_in_region** accepts regions, intermediate regions or
subregions as specified on the `UNStats M49`_ website.


.. |Build_Status| image:: https://travis-ci.org/OCHA-DAP/hdx-python-country.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/OCHA-DAP/hdx-python-country

.. |Coverage_Status| image:: https://coveralls.io/repos/github/OCHA-DAP/hdx-python-country/badge.svg?branch=master
    :alt: Coveralls Build Status
    :target: https://coveralls.io/github/OCHA-DAP/hdx-python-country?branch=master

.. _Humanitarian Data Exchange: https://data.humdata.org/
.. _UNStats M49: https://unstats.un.org/unsd/methodology/m49/overview/
.. _World Bank: http://api.worldbank.org/countries?format=json&per_page=10000