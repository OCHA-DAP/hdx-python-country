[![Build Status](https://travis-ci.org/OCHA-DAP/hdx-python-country.svg?branch=master&ts=1)](https://travis-ci.org/OCHA-DAP/hdx-python-country) [![Coverage Status](https://coveralls.io/repos/github/OCHA-DAP/hdx-python-country/badge.svg?branch=master&ts=1)](https://coveralls.io/github/OCHA-DAP/hdx-python-country?branch=master)

The HDX Python Country Library provides country mappings including ISO 2 and ISO 3 letter codes (ISO 3166) and regions 
using live official data from the [UN OCHA]() feed with fallbacks to an internal static file if there is any problem 
with retrieving data from the url. (Also it is possible to force the use of the internal static files.)

There is a fuzzy matching look up that can handle abbreviations in country names like Dem. for Democratic and Rep. for 
Republic.

Version 2.x.x of the library is a significant change from version 1.x.x which sourced its data from different feeds 
(UN Stats and the World Bank). Consequently, although most of the api calls work the same way in 2.x.x, the ones that 
return full country information do so in a different format to 1.x.x. The format they use is a dictionary using
[Humanitarian Exchange Language]() (HXL) hashtags as keys.

This library is part of the [Humanitarian Data Exchange]() (HDX) project. If you have humanitarian related data, please 
upload your datasets to HDX.

  - [Usage](#usage)
  - [Countries](#countries)

## Usage

The library has detailed API documentation which can be found here: <http://ocha-dap.github.io/hdx-python-country/>. 
The code for the library is here: <https://github.com/ocha-dap/hdx-python-country>.

### Countries

The usage of the country mappings functionality is best illustrated by some examples:

    from hdx.location.country import Country
    
    Country.get_country_name_from_iso3('jpn', use_live=False)  # returns 'Japan'
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