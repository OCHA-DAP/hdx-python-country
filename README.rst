|Build_Status| |Coverage_Status|

The HDX Python Country Library provides country mappings including ISO 2 and ISO 3
letter codes (ISO 3166) and regions (uses World Bank live api with static file fallback)

-  `Usage <#usage>`__
-  `Countries <#countries>`__
-  `Configuring Logging <#configuring-logging>`__

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

    Country.get_country_name_from_iso3('jpn')  # returns 'Japan'
    Country.get_country_name_from_iso2('Pl')  # returns 'Poland'
    Country.get_iso3_country_code('UZBEKISTAN')  # returns 'UZB'

    Country.get_iso3_country_code_partial('Sierra')
    # performs partial match and returns ('SLE', False)

    Country.get_country_info_from_iso2('jp')
    # {'id': 'JPN', 'iso2Code': 'JP', 'name': 'Japan',
    # 'latitude': '35.67', 'longitude': '139.77',
    # 'region': {'value': 'East Asia & Pacific', 'id': 'EAS'},
    # 'adminregion': {'value': '', 'id': ''}, 'capitalCity': 'Tokyo',
    # 'incomeLevel': {'value': 'High income', 'id': 'HIC'},
    # 'lendingType': {'value': 'Not classified', 'id': 'LNX'}}

    Country.get_countries_in_region('South Asia')
    # ['AFG', 'BGD', 'BTN', 'IND', 'LKA', 'MDV', 'NPL', 'PAK']

Valid regions are:

::

    {'EAS': 'East Asia & Pacific', 'SAS': 'South Asia',
    'MEA': 'Middle East & North Africa', 'ECS': 'Europe & Central Asia',
    'LCN': 'Latin America & Caribbean ', 'NAC': 'North America',
    'SSF': 'Sub-Saharan Africa '}

.. |Build_Status| image:: https://travis-ci.org/OCHA-DAP/hdx-python-country.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/OCHA-DAP/hdx-python-country
.. |Coverage_Status| image:: https://coveralls.io/repos/github/OCHA-DAP/hdx-python-country/badge.svg?branch=master
    :alt: Coveralls Build Status
    :target: https://coveralls.io/github/OCHA-DAP/hdx-python-country?branch=master

