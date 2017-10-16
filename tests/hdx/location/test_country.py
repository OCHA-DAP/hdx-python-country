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
    def test_get_country_name_from_iso3(self):
        assert Country.get_country_name_from_iso3('jpn', use_live=False) == 'Japan'
        assert Country.get_country_name_from_iso3('awe', use_live=False) is None
        assert Country.get_country_name_from_iso3('Pol', use_live=False) == 'Poland'
        assert Country.get_country_name_from_iso3('SGP', use_live=False) == 'Singapore'
        assert Country.get_country_name_from_iso3('uy', use_live=False) is None
        with pytest.raises(LocationError):
            Country.get_country_name_from_iso3('uy', use_live=False, exception=LocationError)
        assert Country.get_country_name_from_iso3('uy', use_live=False) is None
        assert Country.get_country_name_from_iso3('VeN', use_live=False) == 'Venezuela, RB'

    def test_get_country_info_from_iso2(self):
        assert Country.get_country_info_from_iso2('jp', use_live=False) == {'name': 'Japan', 'lendingType': {'value': 'Not classified', 'id': 'LNX'}, 'latitude': '35.67', 'incomeLevel': {'value': 'High income', 'id': 'HIC'}, 'id': 'JPN', 'iso2Code': 'JP', 'longitude': '139.77', 'region': {'value': 'East Asia & Pacific', 'id': 'EAS'}, 'adminregion': {'value': '', 'id': ''}, 'capitalCity': 'Tokyo'}
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
        assert Country.get_country_name_from_iso2('VE', use_live=False) == 'Venezuela, RB'

    def test_get_iso3_country_code(self):
        assert Country.get_iso3_country_code('jpn', use_live=False) == 'JPN'
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
        assert Country.get_iso3_country_code_partial('United Kingdom', use_live=False) == ('GBR', True)
        assert Country.get_iso3_country_code_partial('united states', use_live=False) == ('USA', True)
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
        assert len(Country.get_countries_in_region('SSF', use_live=False)) == 48
        assert Country.get_countries_in_region('South Asia', use_live=False) == ['AFG', 'BGD', 'BTN', 'IND', 'LKA',
                                                                  'MDV', 'NPL', 'PAK']
        assert len(Country.get_countries_in_region('NOTEXIST', use_live=False)) == 0
        with pytest.raises(LocationError):
            Country.get_countries_in_region('NOTEXIST', use_live=False, exception=LocationError)

    def test_wb_feed_file_working(self):
        Country.set_data_url(Country._wburl)
        Country._countriesdata = None
        assert len(Country.get_countries_in_region('SSF')) == 48
        json = load_json(script_dir_plus_file('countries.json', TestCountry))
        data = json[1]
        Country.set_countriesdata(data)
        assert Country.get_iso3_country_code('UZBEKISTAN', use_live=False) is None
        Country.set_data_url('NOTEXIST')
        Country._countriesdata = None
        assert Country.get_iso3_country_code('UZBEKISTAN', use_live=True) == 'UZB'
