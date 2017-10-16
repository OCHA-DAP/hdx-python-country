# -*- coding: UTF-8 -*-
"""location Tests"""
import pytest

from hdx.utilities.loader import load_json
from hdx.location.country import Country
from hdx.utilities.path import script_dir_plus_file


class LocationError(Exception):
    pass

class TestCountry:
    @pytest.fixture(scope='class')
    def location(self):
        return Country.set_data_url(None)

    def test_get_country_name_from_iso3(self, location):
        assert Country.get_country_name_from_iso3('jpn') == 'Japan'
        assert Country.get_country_name_from_iso3('awe') is None
        assert Country.get_country_name_from_iso3('Pol') == 'Poland'
        assert Country.get_country_name_from_iso3('SGP') == 'Singapore'
        assert Country.get_country_name_from_iso3('uy') is None
        with pytest.raises(LocationError):
            Country.get_country_name_from_iso3('uy', exception=LocationError)
        assert Country.get_country_name_from_iso3('uy') is None
        assert Country.get_country_name_from_iso3('VeN') == 'Venezuela, RB'

    def test_get_country_info_from_iso2(self, location):
        assert Country.get_country_info_from_iso2('jp') == {'name': 'Japan', 'lendingType': {'value': 'Not classified', 'id': 'LNX'}, 'latitude': '35.67', 'incomeLevel': {'value': 'High income', 'id': 'HIC'}, 'id': 'JPN', 'iso2Code': 'JP', 'longitude': '139.77', 'region': {'value': 'East Asia & Pacific', 'id': 'EAS'}, 'adminregion': {'value': '', 'id': ''}, 'capitalCity': 'Tokyo'}
        assert Country.get_country_info_from_iso2('ab') is None
        with pytest.raises(LocationError):
            Country.get_country_info_from_iso2('ab', exception=LocationError)

    def test_get_country_name_from_iso2(self, location):
        assert Country.get_country_name_from_iso2('jp') == 'Japan'
        assert Country.get_country_name_from_iso2('ab') is None
        assert Country.get_country_name_from_iso2('Pl') == 'Poland'
        assert Country.get_country_name_from_iso2('SG') == 'Singapore'
        assert Country.get_country_name_from_iso2('SGP') is None
        with pytest.raises(LocationError):
            Country.get_country_name_from_iso2('SGP', exception=LocationError)
        assert Country.get_country_name_from_iso2('VE') == 'Venezuela, RB'

    def test_get_iso3_country_code(self, location):
        assert Country.get_iso3_country_code('jpn') == 'JPN'
        assert Country.get_iso3_country_code('jp') == 'JPN'
        assert Country.get_iso3_country_code_partial('jpn') == ('JPN', True)
        assert Country.get_iso3_country_code_partial('ZWE') == ('ZWE', True)
        assert Country.get_iso3_country_code_partial('Vut') == ('VUT', True)
        assert Country.get_iso3_country_code('abc') is None
        with pytest.raises(LocationError):
            Country.get_iso3_country_code('abc', exception=LocationError)
        assert Country.get_iso3_country_code_partial('abc') == (None, False)
        with pytest.raises(LocationError):
            Country.get_iso3_country_code_partial('abc', exception=LocationError)
        assert Country.get_iso3_country_code_partial('United Kingdom') == ('GBR', True)
        assert Country.get_iso3_country_code_partial('united states') == ('USA', True)
        assert Country.get_iso3_country_code('UZBEKISTAN') == 'UZB'
        assert Country.get_iso3_country_code_partial('UZBEKISTAN') == ('UZB', True)
        assert Country.get_iso3_country_code('Sierra') is None
        assert Country.get_iso3_country_code_partial('Sierra') == ('SLE', False)
        assert Country.get_iso3_country_code('Venezuela') is None
        assert Country.get_iso3_country_code_partial('Venezuela') == ('VEN', False)
        with pytest.raises(ValueError):
            Country.get_iso3_country_code('abc', exception=ValueError)
        with pytest.raises(ValueError):
            Country.get_iso3_country_code_partial('abc', exception=ValueError)

    def test_get_countries_in_region(self, location):
        assert len(Country.get_countries_in_region('SSF')) == 48
        assert Country.get_countries_in_region('South Asia') == ['AFG', 'BGD', 'BTN', 'IND', 'LKA',
                                                                  'MDV', 'NPL', 'PAK']
        assert len(Country.get_countries_in_region('NOTEXIST')) == 0
        with pytest.raises(LocationError):
            Country.get_countries_in_region('NOTEXIST', exception=LocationError)

    def test_wb_feed_file_working(self):
        Country.set_data_url(Country._wburl)
        Country._countriesdata = None
        assert len(Country.get_countries_in_region('SSF')) == 48
        json = load_json(script_dir_plus_file('countries.json', TestCountry))
        data = json[1]
        Country.set_countriesdata(data)
        assert Country.get_iso3_country_code('UZBEKISTAN') is None
        Country.set_data_url('NOTEXIST')
        Country._countriesdata = None
        assert Country.get_iso3_country_code('UZBEKISTAN') == 'UZB'
