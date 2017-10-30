# -*- coding: UTF-8 -*-
"""location Tests"""
import pytest

from hdx.utilities.loader import load_json, load_file_to_str
from hdx.location.country import Country, CountryError
from hdx.utilities.path import script_dir_plus_file


class LocationError(Exception):
    pass


class TestCountry:
    def test_get_country_name_from_iso3(self):
        assert Country.get_country_name_from_iso3('jpn', use_live=False) == 'Japan'
        assert Country.get_country_name_from_iso3('awe', use_live=False) is None
        assert Country.get_country_name_from_iso3('Pol', use_live=False) == 'Poland'
        assert Country.get_country_name_from_iso3('SGP', use_live=False) == 'Singapore'
        assert Country.get_country_name_from_iso3('uy', use_live=False) is None
        with pytest.raises(LocationError):
            Country.get_country_name_from_iso3('uy', use_live=False, exception=LocationError)
        assert Country.get_country_name_from_iso3('uy', use_live=False) is None
        assert Country.get_country_name_from_iso3('VeN', use_live=False) == 'Venezuela (Bolivarian Republic of)'

    def test_get_country_info_from_iso2(self):
        assert Country.get_country_info_from_iso2('jp', use_live=False) == {'Sub-region Name': 'Eastern Asia', 'M49 Code': '392', 'ISO-alpha3 Code': 'JPN', 'Developed / Developing Countries': 'Developed', 'Land Locked Developing Countries (LLDC)': '', 'Global Name': 'World', 'Region Name': 'Asia', 'Least Developed Countries (LDC)': '', 'Intermediate Region Code': '', 'Region Code': '142', 'Country or Area': 'Japan', 'Sub-region Code': '030', 'Intermediate Region Name': '', 'Small Island Developing States (SIDS)': '', 'Global Code': '001'}
        assert Country.get_country_info_from_iso2('ab', use_live=False) is None
        with pytest.raises(LocationError):
            Country.get_country_info_from_iso2('ab', use_live=False, exception=LocationError)

    def test_get_country_name_from_iso2(self):
        assert Country.get_country_name_from_iso2('jp', use_live=False) == 'Japan'
        assert Country.get_country_name_from_iso2('ab', use_live=False) is None
        assert Country.get_country_name_from_iso2('Pl', use_live=False) == 'Poland'
        assert Country.get_country_name_from_iso2('SG', use_live=False) == 'Singapore'
        assert Country.get_country_name_from_iso2('SGP', use_live=False) is None
        with pytest.raises(LocationError):
            Country.get_country_name_from_iso2('SGP', use_live=False, exception=LocationError)
        assert Country.get_country_name_from_iso2('VE', use_live=False) == 'Venezuela (Bolivarian Republic of)'

    def test_get_iso3_country_code(self):
        assert Country.get_iso3_country_code('jpn', use_live=False) == 'JPN'
        assert Country.get_iso3_country_code('Dem. Rep. of the Congo', use_live=False) == 'COD'
        assert Country.get_iso3_country_code('Iran (Islamic Rep. of)', use_live=False) == 'IRN'
        assert Country.get_iso3_country_code('United Rep. of Tanzania', use_live=False) == 'TZA'
        assert Country.get_iso3_country_code('United Rep. of Tanzania', use_live=False) == 'TZA'
        assert Country.get_iso3_country_code('Syrian Arab Rep.', use_live=False) == 'SYR'
        assert Country.get_iso3_country_code('Central African Rep.', use_live=False) == 'CAF'
        assert Country.get_iso3_country_code('Rep. of Korea', use_live=False) == 'KOR'
        assert Country.get_iso3_country_code('jp', use_live=False) == 'JPN'
        assert Country.get_iso3_country_code_partial('jpn', use_live=False) == ('JPN', True)
        assert Country.get_iso3_country_code_partial('ZWE', use_live=False) == ('ZWE', True)
        assert Country.get_iso3_country_code_partial('Vut', use_live=False) == ('VUT', True)
        assert Country.get_iso3_country_code('abc', use_live=False) is None
        with pytest.raises(LocationError):
            Country.get_iso3_country_code('abc', use_live=False, exception=LocationError)
        assert Country.get_iso3_country_code_partial('abc', use_live=False) == (None, False)
        with pytest.raises(LocationError):
            Country.get_iso3_country_code_partial('abc', use_live=False, exception=LocationError)
        assert Country.get_iso3_country_code_partial('United Kingdom', use_live=False) == ('GBR', False)
        assert Country.get_iso3_country_code_partial('United Kingdom of Great Britain and Northern Ireland', use_live=False) == ('GBR', True)
        assert Country.get_iso3_country_code_partial('united states', use_live=False) == ('UMI', False)
        assert Country.get_iso3_country_code_partial('united states of america', use_live=False) == ('USA', True)
        assert Country.get_iso3_country_code('UZBEKISTAN', use_live=False) == 'UZB'
        assert Country.get_iso3_country_code_partial('UZBEKISTAN', use_live=False) == ('UZB', True)
        assert Country.get_iso3_country_code('Sierra', use_live=False) is None
        assert Country.get_iso3_country_code_partial('Sierra', use_live=False) == ('SLE', False)
        assert Country.get_iso3_country_code('Venezuela', use_live=False) is None
        assert Country.get_iso3_country_code_partial('Venezuela', use_live=False) == ('VEN', False)
        with pytest.raises(ValueError):
            Country.get_iso3_country_code('abc', use_live=False, exception=ValueError)
        with pytest.raises(ValueError):
            Country.get_iso3_country_code_partial('abc', use_live=False, exception=ValueError)

    def test_get_countries_in_region(self):
        assert len(Country.get_countries_in_region('Africa', use_live=False)) == 60
        assert Country.get_countries_in_region('013', use_live=False) == ['BLZ', 'CRI', 'GTM', 'HND', 'MEX', 'NIC', 'PAN', 'SLV']
        assert Country.get_countries_in_region('Channel Islands', use_live=False) == ['GGY', 'JEY']
        assert len(Country.get_countries_in_region('NOTEXIST', use_live=False)) == 0
        with pytest.raises(LocationError):
            Country.get_countries_in_region('NOTEXIST', use_live=False, exception=LocationError)

    def test_wb_feed_file_working(self):
        json = load_json(script_dir_plus_file('worldbank.json', TestCountry))
        html = load_file_to_str(script_dir_plus_file('unstats.html', TestCountry))
        Country.set_countriesdata(json, html)
        assert Country.get_iso3_country_code('UZBEKISTAN', use_live=False) is None
        assert Country.get_iso3_country_code('south sudan', use_live=False) == 'SSD'
        html = load_file_to_str(script_dir_plus_file('unstats_emptytable.html', TestCountry))
        with pytest.raises(CountryError):
            Country.set_countriesdata(json, html)
        Country.set_worldbank_url()
        Country.set_unstats_url_tablename('NOTEXIST')
        Country._countriesdata = None
        assert Country.get_iso3_country_code('UZBEKISTAN', use_live=True) == 'UZB'
        Country.set_unstats_url_tablename()
        Country.set_worldbank_url('NOTEXIST')
        Country._countriesdata = None
        assert Country.get_iso3_from_iso2('AF') == 'AFG'
        Country.set_unstats_url_tablename(tablename='NOTEXIST')
        Country.set_worldbank_url()
        Country._countriesdata = None
        with pytest.raises(CountryError):
            Country.get_countries_in_region('Caribbean')
        Country.set_unstats_url_tablename()
        Country._countriesdata = None
        assert len(Country.get_countries_in_region('Africa')) == 60
