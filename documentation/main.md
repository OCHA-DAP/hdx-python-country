# Summary

The HDX Python Country Library provides utilities to map between country and region
codes and names and to match administrative level names from different sources.
It also provides utilities for foreign exchange enabling obtaining current and historic
FX rates for different currencies.

# Contents

1. [Information](#information)
2. [Countries](#countries)
3. [Administration Level](#administration-level)
4. [Currencies](#currencies)

# Information

The library provides country mappings including ISO 2 and ISO 3 letter codes (ISO 3166)
and regions using live official data from the [UN OCHA](https://vocabulary.unocha.org/)
feed with fallbacks to an internal static file if there is any problem with retrieving
data from the url. (Also it is possible to force the use of the internal static files.)
The UN OCHA feed has regex taken from
[here](https://github.com/konstantinstadler/country_converter/blob/master/country_converter/country_data.tsv).
with improvements contributed back.

It can exact match English, French, Spanish, Russian, Chinese and Arabic. There is a
fuzzy matching for English look up that can handle abbreviations in country names like
Dem. for Democratic and Rep. for Republic.

Mapping administration level names from a source to a given base set is also handled
including phonetic fuzzy name matching.

It also provides foreign exchange rates and conversion from amounts in local
currency to USD and vice-versa. The conversion relies on Yahoo Finance, falling
back on [currency-api](https://github.com/fawazahmed0/currency-api) for current rates, and Yahoo Finance falling back
on IMF data via IATI (with interpolation) for historic daily rates.

This library is part of the [Humanitarian Data Exchange](https://data.humdata.org/)
(HDX) project. If you have humanitarian related data, please upload your datasets to
HDX.

The code for the library is [here](https://github.com/OCHA-DAP/hdx-python-country).
The library has detailed API documentation which can be found in the menu at the top.

## Breaking Changes
From 3.7.5, removed clean_name function. There is now a function normalise in
HDX Python Utilities.

From 3.5.5, after creating an Adminlevel, call either setup_from_admin_info,
setup_from_libhxl_dataset or setup_from_url.

From 3.4.6, Python 3.7 no longer supported

From 3.3.2, major update to foreign exchange code and use of new Yahoo data source

From 3.0.0, only supports Python >= 3.6

Version 2.x.x of the library is a significant change from version 1.x.x which sourced
its data from different feeds (UN Stats and the World Bank). Consequently, although
most of the api calls work the same way in 2.x.x, the ones that return full country
information do so in a different format to 1.x.x. The format they use is a dictionary
using [Humanitarian Exchange Language](https://hxlstandard.org/) (HXL) hashtags as keys.

# Description of Utilities

## Countries

The usage of the country mappings functionality is best illustrated by some examples:

    from hdx.location.country import Country

    Country.countriesdata(use_live=False, country_name_overrides={"PSE": "oPt"})
    # Set up using non live data from repo rather and override default country name
    # (Leaving out this step will use live data and no overrides)
    Country.get_country_name_from_iso3("jpn", use_live=False)  # returns "Japan"
    Country.get_country_name_from_iso3("vEn", formal=True)  # returns "the Bolivarian Republic of Venezuela"
    # uselive=False forces the use of internal files instead of accessing the live feeds.
    # It only needs to be supplied to the first call as the data once loaded is held
    # in internal dictionaries for future use.
    Country.get_country_name_from_iso2("Pl")  # returns "Poland"
    Country.get_iso3_country_code("UZBEKISTAN")  # returns "UZB"
    Country.get_country_name_from_m49(4)  # returns "Afghanistan"

    Country.get_iso3_country_code_fuzzy("Sierra")
    # performs fuzzy match and returns ("SLE", False). The False indicates a fuzzy rather than exact match.
    assert Country.get_iso3_country_code_fuzzy("Czech Rep.")
    # returns ("CZE", False)

    Country.get_country_info_from_iso2("jp")
    # Returns dictionary with HXL hashtags as keys. For more on HXL, see http://hxlstandard.org/
    # {"#country+alt+i_ar+name+v_unterm": "اليابان", "#country+alt+i_en+name+v_unterm": "Japan",
    # "#country+alt+i_es+name+v_unterm": "Japón (el)", "#country+alt+i_fr+name+v_unterm": "Japon (le)",
    # "#country+alt+i_ru+name+v_unterm": "Япония", "#country+alt+i_zh+name+v_unterm": "日本",
    # "#country+alt+name+v_dgacm"": "", "#country+alt+name+v_fts": "",
    # "#country+alt+name+v_hrinfo_country": "", "#country+alt+name+v_iso": "",
    # "#country+alt+name+v_m49": "", "#country+alt+name+v_reliefweb": "",
    # "#country+code+num+v_m49": "392", "#country+code+v_fts": "112",
    # "#country+code+v_hrinfo_country": "292", "#country+code+v_iso2": "JP",
    # "#country+code+v_iso3": "JPN", "#country+code+v_reliefweb": "128",
    # "#country+formal+i_en+name+v_unterm": "Japan", "#country+name+preferred": "Japan",
    # "#country+name+short+v_reliefweb": "", "#country+regex": "japan", "#date+start": "1974-01-01",
    # "#geo+admin_level": "0", "#geo+lat": "37.63209801", "#geo+lon": "138.0812256", "#meta+id": "112",
    # "#region+code+intermediate": "", "#region+code+main": "142", "#region+code+sub": "30",
    # "#region+intermediate+name+preferred": "", "#region+main+name+preferred": "Asia",
    # "#region+name+preferred+sub": "Eastern Asia"}
    Country.get_countries_in_region("Channel Islands")
    # ["GGY", "JEY"]
    len(Country.get_countries_in_region("Africa"))
    # 60
    Country.get_countries_in_region(13)
    # ["BLZ", "CRI", "GTM", "HND", "MEX", "NIC", "PAN", "SLV"]

## Administration Level

The administration level mappings takes input configuration dictionary,
*admin_config*, which defaults to an empty dictionary.

*admin_config* can have the following optional keys:

*countries_fuzzy_try* are countries (iso3 codes) for which to try fuzzy
matching. Default is all countries.
*admin_name_mappings* is a dictionary of mappings from name to pcode. These can
be global or they can be restricted by country or parent (if the AdminLevel
object has been set up with parents). Keys take the form "MAPPING",
"AFG|MAPPING" or "AF01|MAPPING".
*admin_name_replacements* is a dictionary of textual replacements to try when
fuzzy matching. It maps from string to string replacement. The replacements can
be global or they can be restricted by country or parent (if the AdminLevel
object has been set up with parents). Keys take the form "STRING_TO_REPLACE",
"AFG|STRING_TO_REPLACE" or "AF01|STRING_TO_REPLACE".
*admin_fuzzy_dont* is a list of names for which fuzzy matching should not be
tried

Once an AdminLevel object is constructed, one of three setup methods must be
called: *setup_from_admin_info*, *setup_from_libhxl_dataset* or
*setup_from_url*.

Method *setup_from_admin_info* takes key *admin_info* which is a list with
values of the form:

    {"iso3": "AFG", "pcode": "AF01", "name": "Kabul"}
    {"iso3": "AFG", "pcode": "AF0101", "name": "Kabul", "parent": "AF01"}

Dictionaries *pcode_to_name* and *pcode_to_iso3* are populated in the
AdminLevel object. *parent* is optional, but if provided enables lookup of
location names by both country and parent rather than just country which should
help with any name clashes. It also results in the population of a dictionary
in the AdminLevel object *pcode_to_parent*.

Method *setup_from_libhxl_dataset* takes a libhxl Dataset object, while
*setup_from_url* takes a URL which defaults to a resource in the global p-codes
dataset on HDX.

These methods also have optional parameter *countryiso3s* which is a tuple or
list of country ISO3 codes to be read or None if all countries are desired.

Examples of usage:

    AdminLevel.looks_like_pcode("YEM123")  # returns True
    AdminLevel.looks_like_pcode("Yemen")  # returns False
    AdminLevel.looks_like_pcode("YEME123")  # returns False
    adminlevel = AdminLevel(config)
    adminlevel.setup_from_admin_info(admin_info, countryiso3s=("YEM",))
    adminlevel.get_pcode("YEM", "YEM030", logname="test")  # returns ("YE30", True)
    adminlevel.get_pcode("YEM", "Al Dhale"e / الضالع")  # returns ("YE30", False)
    adminlevel.get_pcode("YEM", "Al Dhale"e / الضالع", fuzzy_match=False)  # returns (None, True)
    assert admintwo.get_pcode("AFG", "Kabul", parent="AF01") == ("AF0101", True)

There is basic admin 1 p-code length conversion by default. A more advanced
p-code length conversion can be activated by calling *load_pcode_formats*
which takes a URL that defaults to a resource in the global p-codes dataset on
HDX:

    admintwo.load_pcode_formats()
    admintwo.get_pcode("YEM", "YEM30001")  # returns ("YE3001", True)

The length conversion can be further enhanced by supplying either parent
AdminLevel objects in a list or lists of p-codes per parent admin level:

    admintwo.set_parent_admins_from_adminlevels([adminone])
    admintwo.get_pcode("NER", "NE00409")  # returns ("NER004009", True)
    admintwo.set_parent_admins([adminone.pcodes])
    admintwo.get_pcode("NER", "NE00409")  # returns ("NER004009", True)

## Currencies

Various functions support the conversion of monetary amounts to USD. Note that the
returned values are cached to reduce network usage which means that the library is
unsuited for use where rates are expected to update while the program is running:

    Currency.setup(fallback_historic_to_current=True, fallback_current_to_static=True, log_level=logging.INFO)
    currency = Country.get_currency_from_iso3("usa")  # returns "USD"
    assert Currency.get_current_rate("usd")  # returns 1
    Currency.get_current_value_in_usd(10, currency)  # returns 10
    gbprate = Currency.get_current_value_in_usd(10, "gbp")
    assert gbprate != 10
    Currency.get_current_value_in_currency(gbprate, "GBP")  # returns 10
    date = parse_date("2020-02-20")
    Currency.get_historic_rate("gbp", date)  # returns 0.7735000252723694
    Currency.get_historic_rate("gbp", parse_date("2020-02-20 00:00:00 NZST"),
                               ignore_timeinfo=False)  # returns 0.76910001039505
    Currency.get_historic_value_in_usd(10, "USD", date)  # returns 10
    Currency.get_historic_value_in_usd(10, "gbp", date)  # returns 13.002210200027791
    Currency.get_historic_value_in_currency(10, "gbp", date)  # returns 7.735000252723694
    Currency.get_historic_rate("gbp", parse_date("2020-02-20 00:00:00 NZST",
                               timezone_handling=2), ignore_timeinfo=False)
    # == 0.76910001039505

Historic daily rates can be made to fall back to current rates if desired (this
is not the default). It is possible to pass in a Retrieve object to
Currency.setup() to allow the downloaded files from the secondary sources to be
saved or previously downloaded files to be reused and to allow fallbacks from
current rates to a static file eg.

    Currency.setup(retriever, ..., fallback_historic_to_current=True, fallback_current_to_static=True)
