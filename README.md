[![Build Status](https://github.com/OCHA-DAP/hdx-python-country/workflows/build/badge.svg)](https://github.com/OCHA-DAP/hdx-python-country/actions?query=workflow%3Abuild) [![Coverage Status](https://coveralls.io/repos/github/OCHA-DAP/hdx-python-country/badge.svg?branch=master&ts=1)](https://coveralls.io/github/OCHA-DAP/hdx-python-country?branch=master)

The HDX Python Country Library provides country mappings including ISO 2 and ISO 3 letter codes (ISO 3166) and regions 
using live official data from the [UN OCHA](https://vocabulary.unocha.org/) feed with fallbacks to an internal static 
file if there is any problem with retrieving data from the url. (Also it is possible to force the use of the internal 
static files.)

It can exact match English, French, Spanish, Russian, Chinese and Arabic. There is a fuzzy matching for English look up 
that can handle abbreviations in country names like Dem. for Democratic and Rep. for Republic.

Mapping administration level one names from a source to a given base set is also handled including phonetic fuzzy name 
matching if you are running Python 3.  

It also provides currency conversion to USD from local currency.

Version 2.x.x of the library is a significant change from version 1.x.x which sourced its data from different feeds 
(UN Stats and the World Bank). Consequently, although most of the api calls work the same way in 2.x.x, the ones that 
return full country information do so in a different format to 1.x.x. The format they use is a dictionary using
[Humanitarian Exchange Language](https://hxlstandard.org/) (HXL) hashtags as keys.

This library is part of the [Humanitarian Data Exchange](https://data.humdata.org/) (HDX) project. If you have 
humanitarian related data, please upload your datasets to HDX.

  - [Usage](#usage)
  - [Examples](#examples)

## Usage

The library has detailed API documentation which can be found here: <http://ocha-dap.github.io/hdx-python-country/>. 
The code for the library is here: <https://github.com/ocha-dap/hdx-python-country>.

### Examples

The usage of the country mappings functionality is best illustrated by some examples:

    from hdx.location.country import Country
    
    Country.countriesdata(use_live=False, country_name_overrides={'PSE': 'oPt'})
    # Set up using non live data from repo rather and override default country name
    # (Leaving out this step will use live data and no overrides)
    Country.get_country_name_from_iso3('jpn', use_live=False)  # returns 'Japan'
    Country.get_country_name_from_iso3('vEn', shortname=True)  # returns 'Venezuela'
    # uselive=False forces the use of internal files instead of accessing the live feeds.
    # It only needs to be supplied to the first call as the data once loaded is held
    # in internal dictionaries for future use.
    Country.get_country_name_from_iso2('Pl')  # returns 'Poland'
    Country.get_iso3_country_code('UZBEKISTAN')  # returns 'UZB'
    Country.get_country_name_from_m49(4)  # returns 'Afghanistan'
    
    Country.get_iso3_country_code_fuzzy('Sierra')
    # performs fuzzy match and returns ('SLE', False). The False indicates a fuzzy rather than exact match.
    assert Country.get_iso3_country_code_fuzzy('Czech Rep.')
    # returns ('CZE', False)
    
    Country.get_country_info_from_iso2('jp')
    # Returns dictionary with HXL hashtags as keys. For more on HXL, see http://hxlstandard.org/
    # {'#country+alt+i_ar+name+v_unterm': 'اليابان', '#country+alt+i_en+name+v_unterm': 'Japan',
    # '#country+alt+i_es+name+v_unterm': 'Japón (el)', '#country+alt+i_fr+name+v_unterm': 'Japon (le)',
    # '#country+alt+i_ru+name+v_unterm': 'Япония', '#country+alt+i_zh+name+v_unterm': '日本',
    # '#country+alt+name+v_fts': '', '#country+alt+name+v_hrinfo_country': '',
    # '#country+alt+name+v_iso': '', '#country+alt+name+v_m49': '',
    # '#country+alt+name+v_reliefweb': '', '#country+alt+name+v_unterm': '',
    # '#country+code+num+v_m49': '392', '#country+code+v_fts': '112',
    # '#country+code+v_hrinfo_country': '292', '#country+code+v_iso2': 'JP',
    # '#country+code+v_iso3': 'JPN', '#country+code+v_reliefweb': '128',
    # '#country+name+preferred': 'Japan', '#country+name+short+v_reliefweb': '',
    # '#country+regex': 'japan', '#geo+admin_level': '0', '#geo+lat': '37.63209801',
    # '#geo+lon': '138.0812256', '#meta+id': '112', '#region+code+intermediate': '',
    # '#region+code+main': '142', '#region+code+sub': '30', '#region+intermediate+name+preferred': '',
    # '#region+main+name+preferred': 'Asia', '#region+name+preferred+sub': 'Eastern Asia'}
    Country.get_countries_in_region('Channel Islands')
    # ['GGY', 'JEY']
    len(Country.get_countries_in_region('Africa'))
    # 60
    Country.get_countries_in_region(13)
    # ['BLZ', 'CRI', 'GTM', 'HND', 'MEX', 'NIC', 'PAN', 'SLV']
    
The administration level one mappings requires using an input configuration dictionary, admin_config, with key 
*admin1_info* which is a list with values of the form:

    {'iso3': 'AFG', 'pcode': 'AF01', 'name': 'Kabul'}

Various other keys are optional:

*countries_fuzzy_try* are countries (iso3 codes) for which to try fuzzy matching. Default is all countries.
*admin1_name_mappings* is a dictionary of mappings from name to pcode (for where fuzzy matching fails)
*admin1_name_replacements* is a dictionary of textual replacements to try when fuzzy matching
*admin1_fuzzy_dont* is a list of names for which fuzzy matching should not be tried

Examples of usage:

    adminone = AdminOne(config)
    adminone.get_pcode('YEM', 'YEM030', scrapername='test')  # returns ('YE30', True)
    # Fuzzy matching in Python 3 only
    adminone.get_pcode('YEM', "Al Dhale'e / الضالع", scrapername='test')  # returns ('YE30', False)

Currency conversion to USD is simple:

    currency = Country.get_currency_from_iso3('usa')  # returns 'USD'
    Currency.get_current_value_in_usd(10, currency)  # returns 10
    gbprate = Currency.get_current_value_in_usd(10, 'gbp')
    assert gbprate != 10
    Currency.get_current_value_in_currency(gbprate, 'GBP')  # returns 10
    date = parse_date('2020-02-20')
    Currency.get_historic_value_in_usd(10, 'USD', date)  # returns 10
    Currency.get_historic_value_in_usd(10, 'gbp', date)  # returns 12.877
    Currency.get_historic_value_in_currency(10, 'gbp', date)  # returns 7.765783955890346
    
It is also possible to pass in a Retrieve object to Currency.setup() to allow the downloaded files to be saved or 
previously downloaded files to be reused. It is also possible to change the urls used for current and historic rates
(the defaults are current_rates_url: https://api.exchangerate.host/latest?base=usd, 
historic_rates_url: https://codeforiati.org/exchangerates-scraper/consolidated.csv) and to activate fallbacks from 
current rates to a static file and/or from historic rates to current rates (for which more currencies exist).

    Currency.setup(retriever, current_rates_url=my_current_rates_url, historic_rates_url=my_historic_rates_url,
                   fallback_historic_to_current=True, fallback_current_to_static=True)

