# -*- coding: UTF-8 -*-
"""location Tests"""
import hxl
import pytest
from hdx.utilities.path import script_dir_plus_file

from hdx.location.country import Country


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
        assert Country.get_country_name_from_iso3('TWN', use_live=False) == 'Taiwan (Province of China)'

    def test_get_iso2_from_iso3(self):
        assert Country.get_iso2_from_iso3('jpn', use_live=False) == 'JP'
        assert Country.get_iso2_from_iso3('abc', use_live=False) is None
        with pytest.raises(LocationError):
            Country.get_iso2_from_iso3('abc', use_live=False, exception=LocationError)

    def test_get_iso3_from_iso2(self):
        assert Country.get_iso3_from_iso2('jp', use_live=False) == 'JPN'
        assert Country.get_iso3_from_iso2('ab', use_live=False) is None
        with pytest.raises(LocationError):
            Country.get_iso3_from_iso2('ab', use_live=False, exception=LocationError)

    def test_get_country_info_from_iso3(self):
        assert Country.get_country_info_from_iso3('bih', use_live=False) == {
            '#country+alt+i_ar+name+v_unterm': 'البوسنة والهرسك',
            '#country+alt+i_en+name+v_unterm': 'Bonaire, Saint Eustatius and Saba',
            '#country+alt+i_es+name+v_unterm': 'Bosnia y Herzegovina',
            '#country+alt+i_fr+name+v_unterm': 'Bosnie-Herzégovine (la)',
            '#country+alt+i_ru+name+v_unterm': 'Босния и Герцеговина',
            '#country+alt+i_zh+name+v_unterm': '波斯尼亚和黑塞哥维那',
            '#country+alt+name+v_fts': '',
            '#country+alt+name+v_hrinfo_country': '',
            '#country+alt+name+v_iso': '',
            '#country+alt+name+v_m49': '',
            '#country+alt+name+v_reliefweb': '',
            '#country+alt+name+v_unterm': '',
            '#country+code+num+v_m49': '70',
            '#country+code+v_fts': '28',
            '#country+code+v_hrinfo_country': '208',
            '#country+code+v_iso2': 'BA',
            '#country+code+v_iso3': 'BIH',
            '#country+code+v_reliefweb': '40',
            '#country+name+preferred': 'Bosnia and Herzegovina',
            '#country+name+short+v_reliefweb': '',
            '#country+regex': 'herzegovina|bosnia',
            '#geo+admin_level': '0',
            '#geo+lat': '44.16506495',
            '#geo+lon': '17.79105724',
            '#meta+id': '28',
            '#region+code+intermediate': '',
            '#region+code+main': '150',
            '#region+code+sub': '39',
            '#region+intermediate+name+preferred': '',
            '#region+main+name+preferred': 'Europe',
            '#region+name+preferred+sub': 'Southern Europe'}

    def test_get_country_info_from_iso2(self):
        assert Country.get_country_info_from_iso2('jp', use_live=False) == {
            '#country+alt+i_ar+name+v_unterm': 'اليابان',
            '#country+alt+i_en+name+v_unterm': 'Japan',
            '#country+alt+i_es+name+v_unterm': 'Japón (el)',
            '#country+alt+i_fr+name+v_unterm': 'Japon (le)',
            '#country+alt+i_ru+name+v_unterm': 'Япония',
            '#country+alt+i_zh+name+v_unterm': '日本',
            '#country+alt+name+v_fts': '',
            '#country+alt+name+v_hrinfo_country': '',
            '#country+alt+name+v_iso': '',
            '#country+alt+name+v_m49': '',
            '#country+alt+name+v_reliefweb': '',
            '#country+alt+name+v_unterm': '',
            '#country+code+num+v_m49': '392',
            '#country+code+v_fts': '112',
            '#country+code+v_hrinfo_country': '292',
            '#country+code+v_iso2': 'JP',
            '#country+code+v_iso3': 'JPN',
            '#country+code+v_reliefweb': '128',
            '#country+name+preferred': 'Japan',
            '#country+name+short+v_reliefweb': '',
            '#country+regex': 'japan',
            '#geo+admin_level': '0',
            '#geo+lat': '37.63209801',
            '#geo+lon': '138.0812256',
            '#meta+id': '112',
            '#region+code+intermediate': '',
            '#region+code+main': '142',
            '#region+code+sub': '30',
            '#region+intermediate+name+preferred': '',
            '#region+main+name+preferred': 'Asia',
            '#region+name+preferred+sub': 'Eastern Asia'}
        assert Country.get_country_info_from_iso2('ab', use_live=False) is None
        assert Country.get_country_info_from_iso2('TW', use_live=False) == {
            '#country+alt+i_ar+name+v_unterm': '',
            '#country+alt+i_en+name+v_unterm': 'Taiwan',
            '#country+alt+i_es+name+v_unterm': '',
            '#country+alt+i_fr+name+v_unterm': '',
            '#country+alt+i_ru+name+v_unterm': '',
            '#country+alt+i_zh+name+v_unterm': '',
            '#country+alt+name+v_fts': 'Taiwan, Province of China',
            '#country+alt+name+v_hrinfo_country': 'Taiwan, Province of China',
            '#country+alt+name+v_iso': '',
            '#country+alt+name+v_m49': '',
            '#country+alt+name+v_reliefweb': 'China - Taiwan Province',
            '#country+alt+name+v_unterm': '',
            '#country+code+num+v_m49': '158',
            '#country+code+v_fts': '219',
            '#country+code+v_hrinfo_country': '399',
            '#country+code+v_iso2': 'TW',
            '#country+code+v_iso3': 'TWN',
            '#country+code+v_reliefweb': '61',
            '#country+name+preferred': 'Taiwan (Province of China)',
            '#country+name+short+v_reliefweb': '',
            '#country+regex': '.*taiwan|.*taipei|.*formosa|^(?!.*\\bdem)(?!.*\\bpe)(?!.*\\bdr)(^rep.*).*\\bchina.*(?!.*\\bdem.*)(?!\\bpe.*)(?!.*\\bdr.*).*|^ROC$',
            '#geo+admin_level': '0',
            '#geo+lat': '23.74652012',
            '#geo+lon': '120.9621301',
            '#meta+id': '218',
            '#region+code+intermediate': '',
            '#region+code+main': '142',
            '#region+code+sub': '30',
            '#region+intermediate+name+preferred': '',
            '#region+main+name+preferred': 'Asia',
            '#region+name+preferred+sub': 'Eastern Asia'}
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
        assert Country.get_country_name_from_iso2('TW', use_live=False) == 'Taiwan (Province of China)'

    def test_get_m49_from_iso3(self):
        assert Country.get_m49_from_iso3('AFG', use_live=False) == 4
        assert Country.get_m49_from_iso3('WSM', use_live=False) == 882
        assert Country.get_m49_from_iso3('TWN', use_live=False) is 158
        assert Country.get_m49_from_iso3('ABC', use_live=False) is None
        with pytest.raises(LocationError):
            Country.get_m49_from_iso3('ABC', use_live=False, exception=LocationError)

    def test_get_iso3_from_m49(self):
        assert Country.get_iso3_from_m49(4, use_live=False) == 'AFG'
        assert Country.get_iso3_from_m49(882, use_live=False) == 'WSM'
        assert Country.get_iso3_from_m49(9999, use_live=False) is None
        with pytest.raises(LocationError):
            Country.get_iso3_from_m49(9999, use_live=False, exception=LocationError)

    def test_get_country_info_from_m49(self):
        assert Country.get_country_info_from_m49(4, use_live=False) == {
            '#country+alt+i_ar+name+v_unterm': 'أفغانستان',
            '#country+alt+i_en+name+v_unterm': 'Afghanistan',
            '#country+alt+i_es+name+v_unterm': 'Afganistán (el)',
            '#country+alt+i_fr+name+v_unterm': "Afghanistan (l') [masc.]",
            '#country+alt+i_ru+name+v_unterm': 'Афганистан',
            '#country+alt+i_zh+name+v_unterm': '阿富汗',
            '#country+alt+name+v_fts': '',
            '#country+alt+name+v_hrinfo_country': '',
            '#country+alt+name+v_iso': '',
            '#country+alt+name+v_m49': '',
            '#country+alt+name+v_reliefweb': '',
            '#country+alt+name+v_unterm': '',
            '#country+code+num+v_m49': '4',
            '#country+code+v_fts': '1',
            '#country+code+v_hrinfo_country': '181',
            '#country+code+v_iso2': 'AF',
            '#country+code+v_iso3': 'AFG',
            '#country+code+v_reliefweb': '13',
            '#country+name+preferred': 'Afghanistan',
            '#country+name+short+v_reliefweb': '',
            '#country+regex': 'afghan',
            '#geo+admin_level': '0',
            '#geo+lat': '33.83147477',
            '#geo+lon': '66.02621828',
            '#meta+id': '1',
            '#region+code+intermediate': '',
            '#region+code+main': '142',
            '#region+code+sub': '34',
            '#region+intermediate+name+preferred': '',
            '#region+main+name+preferred': 'Asia',
            '#region+name+preferred+sub': 'Southern Asia'}
        assert Country.get_country_info_from_m49(882, use_live=False) == {
            '#country+alt+i_ar+name+v_unterm': 'ساموا',
            '#country+alt+i_en+name+v_unterm': 'Samoa',
            '#country+alt+i_es+name+v_unterm': 'Samoa',
            '#country+alt+i_fr+name+v_unterm': 'Samoa (le)',
            '#country+alt+i_ru+name+v_unterm': 'Самоа',
            '#country+alt+i_zh+name+v_unterm': '萨摩亚',
            '#country+alt+name+v_fts': '',
            '#country+alt+name+v_hrinfo_country': '',
            '#country+alt+name+v_iso': '',
            '#country+alt+name+v_m49': '',
            '#country+alt+name+v_reliefweb': '',
            '#country+alt+name+v_unterm': '',
            '#country+code+num+v_m49': '882',
            '#country+code+v_fts': '193',
            '#country+code+v_hrinfo_country': '373',
            '#country+code+v_iso2': 'WS',
            '#country+code+v_iso3': 'WSM',
            '#country+code+v_reliefweb': '204',
            '#country+name+preferred': 'Samoa',
            '#country+name+short+v_reliefweb': '',
            '#country+regex': '^(?!.*amer.*)samoa|(\\bindep.*samoa)',
            '#geo+admin_level': '0',
            '#geo+lat': '-13.16992041',
            '#geo+lon': '-173.5139768',
            '#meta+id': '192',
            '#region+code+intermediate': '',
            '#region+code+main': '9',
            '#region+code+sub': '61',
            '#region+intermediate+name+preferred': '',
            '#region+main+name+preferred': 'Oceania',
            '#region+name+preferred+sub': 'Polynesia'}

        assert Country.get_country_info_from_m49(9999, use_live=False) is None
        with pytest.raises(LocationError):
            Country.get_country_info_from_m49(9999, use_live=False, exception=LocationError)

    def test_get_country_name_from_m49(self):
        assert Country.get_country_name_from_m49(4, use_live=False) == 'Afghanistan'
        assert Country.get_country_name_from_m49(882, use_live=False) == 'Samoa'
        assert Country.get_country_name_from_m49(9999, use_live=False) is None
        with pytest.raises(LocationError):
            Country.get_country_name_from_m49(9999, use_live=False, exception=LocationError)

    def test_expand_countryname_abbrevs(self):
        assert Country.expand_countryname_abbrevs('jpn') == ['JPN']
        assert Country.expand_countryname_abbrevs('Haha Dem. Fed. Republic') == ['HAHA DEMOCRATIC FED. REPUBLIC',
                                                                             'HAHA DEMOCRATIC FEDERATION REPUBLIC',
                                                                             'HAHA DEMOCRATIC FEDERAL REPUBLIC',
                                                                             'HAHA DEMOCRATIC FEDERATED REPUBLIC']

    def test_simplify_countryname(self):
        assert Country.simplify_countryname('jpn') == ('JPN', list())
        assert Country.simplify_countryname('United Rep. of Tanzania') == ('TANZANIA', ['UNITED', 'REP', 'OF'])
        assert Country.simplify_countryname('Micronesia (Federated States of)') == ('MICRONESIA', ['FEDERATED', 'STATES', 'OF'])
        assert Country.simplify_countryname('Dem. Rep. of the Congo') == ('CONGO', ['DEM', 'REP', 'OF', 'THE'])
        assert Country.simplify_countryname("Korea, Democratic People's Republic of") == ('KOREA', ['DEMOCRATIC', "PEOPLE'S", 'REPUBLIC', 'OF'])
        assert Country.simplify_countryname("Democratic People's Republic of Korea") == ('KOREA', ['DEMOCRATIC', "PEOPLE'S", 'REPUBLIC', 'OF'])
        assert Country.simplify_countryname('The former Yugoslav Republic of Macedonia') == ('MACEDONIA', ['THE', 'FORMER', 'YUGOSLAV', 'REPUBLIC', 'OF'])

    def test_get_iso3_country_code(self):
        assert Country.get_iso3_country_code('jpn', use_live=False) == 'JPN'
        assert Country.get_iso3_country_code('Dem. Rep. of the Congo', use_live=False) == 'COD'
        assert Country.get_iso3_country_code('Russian Fed.', use_live=False) == 'RUS'
        assert Country.get_iso3_country_code('Micronesia (Federated States of)', use_live=False) == 'FSM'
        assert Country.get_iso3_country_code('Iran (Islamic Rep. of)', use_live=False) == 'IRN'
        assert Country.get_iso3_country_code('United Rep. of Tanzania', use_live=False) == 'TZA'
        assert Country.get_iso3_country_code('Syrian Arab Rep.', use_live=False) == 'SYR'
        assert Country.get_iso3_country_code('Central African Rep.', use_live=False) == 'CAF'
        assert Country.get_iso3_country_code('Rep. of Korea', use_live=False) == 'KOR'
        assert Country.get_iso3_country_code('St. Pierre and Miquelon', use_live=False) == 'SPM'
        assert Country.get_iso3_country_code('Christmas Isl.', use_live=False) == 'CXR'
        assert Country.get_iso3_country_code('Cayman Isl.', use_live=False) == 'CYM'
        assert Country.get_iso3_country_code('jp', use_live=False) == 'JPN'
        assert Country.get_iso3_country_code('Taiwan (Province of China)', use_live=False) == 'TWN'
        assert Country.get_iso3_country_code_fuzzy('jpn', use_live=False) == ('JPN', True)
        assert Country.get_iso3_country_code_fuzzy('ZWE', use_live=False) == ('ZWE', True)
        assert Country.get_iso3_country_code_fuzzy('Vut', use_live=False) == ('VUT', True)
        assert Country.get_iso3_country_code('abc', use_live=False) is None
        with pytest.raises(LocationError):
            Country.get_iso3_country_code('abc', use_live=False, exception=LocationError)
        assert Country.get_iso3_country_code_fuzzy('abc', use_live=False) == (None, False)
        with pytest.raises(LocationError):
            Country.get_iso3_country_code_fuzzy('abc', use_live=False, exception=LocationError)
        assert Country.get_iso3_country_code_fuzzy('United Kingdom', use_live=False) == ('GBR', False)
        assert Country.get_iso3_country_code_fuzzy('United Kingdom of Great Britain and Northern Ireland', use_live=False) == ('GBR', True)
        assert Country.get_iso3_country_code_fuzzy('united states', use_live=False) == ('USA', False)
        assert Country.get_iso3_country_code_fuzzy('united states of america', use_live=False) == ('USA', True)
        assert Country.get_iso3_country_code('UZBEKISTAN', use_live=False) == 'UZB'
        assert Country.get_iso3_country_code_fuzzy('UZBEKISTAN', use_live=False) == ('UZB', True)
        assert Country.get_iso3_country_code('Sierra', use_live=False) is None
        assert Country.get_iso3_country_code_fuzzy('Sierra', use_live=False) == ('SLE', False)
        assert Country.get_iso3_country_code('Venezuela', use_live=False) is None
        assert Country.get_iso3_country_code_fuzzy('Venezuela', use_live=False) == ('VEN', False)
        assert Country.get_iso3_country_code_fuzzy('Heard Isl.', use_live=False) == ('HMD', False)
        assert Country.get_iso3_country_code_fuzzy('Falkland Isl.', use_live=False) == ('FLK', False)
        assert Country.get_iso3_country_code_fuzzy('Czech Republic', use_live=False) == ('CZE', False)
        assert Country.get_iso3_country_code_fuzzy('Czech Rep.', use_live=False) == ('CZE', False)
        assert Country.get_iso3_country_code_fuzzy('Islamic Rep. of Iran', use_live=False) == ('IRN', False)
        assert Country.get_iso3_country_code_fuzzy('Dem. Congo', use_live=False) == ('COD', False)
        assert Country.get_iso3_country_code_fuzzy('Congo, Republic of', use_live=False) == ('COG', False)
        assert Country.get_iso3_country_code_fuzzy('Republic of the Congo', use_live=False) == ('COG', False)
        assert Country.get_iso3_country_code_fuzzy('Vietnam', use_live=False) == ('VNM', False)
        assert Country.get_iso3_country_code_fuzzy('South Korea', use_live=False) == ('KOR', False)
        assert Country.get_iso3_country_code_fuzzy('Korea Republic', use_live=False) == ('KOR', False)
        assert Country.get_iso3_country_code_fuzzy('Dem. Republic Korea', use_live=False) == ('PRK', False)
        assert Country.get_iso3_country_code_fuzzy('North Korea', use_live=False) == ('PRK', False)
        assert Country.get_iso3_country_code_fuzzy('Serbia and Kosovo: S/RES/1244 (1999)', use_live=False) == ('SRB', False)
        assert Country.get_iso3_country_code_fuzzy('U.S. Virgin Islands', use_live=False) == ('VIR', True)
        assert Country.get_iso3_country_code_fuzzy('U.K. Virgin Islands', use_live=False) == ('VGB', False)
        assert Country.get_iso3_country_code_fuzzy('Taiwan', use_live=False) == ('TWN', False)
        with pytest.raises(ValueError):
            Country.get_iso3_country_code('abc', use_live=False, exception=ValueError)
        with pytest.raises(ValueError):
            Country.get_iso3_country_code_fuzzy('abc', use_live=False, exception=ValueError)

    def test_get_countries_in_region(self):
        assert Country.get_countries_in_region('Eastern Asia', use_live=False) == ['CHN', 'HKG', 'JPN', 'KOR', 'MAC',
                                                                                   'MNG', 'PRK', 'TWN']
        assert len(Country.get_countries_in_region('Africa', use_live=False)) == 60
        assert Country.get_countries_in_region(13, use_live=False) == ['BLZ', 'CRI', 'GTM', 'HND', 'MEX', 'NIC', 'PAN',
                                                                       'SLV']
        assert Country.get_countries_in_region('Channel Islands', use_live=False) == ['GGY', 'JEY']
        assert len(Country.get_countries_in_region('NOTEXIST', use_live=False)) == 0
        with pytest.raises(LocationError):
            Country.get_countries_in_region('NOTEXIST', use_live=False, exception=LocationError)

    def test_ocha_feed_file_working(self):
        countries = hxl.data(script_dir_plus_file('Countries_UZB_Deleted.csv', TestCountry), allow_local=True)
        Country.set_countriesdata(countries)
        assert Country.get_iso3_country_code('UZBEKISTAN', use_live=False) is None
        assert Country.get_iso3_country_code('south sudan', use_live=False) == 'SSD'
        Country.set_ocha_url()
        Country._countriesdata = None
        assert Country.get_iso3_country_code('UZBEKISTAN', use_live=True) == 'UZB'
        Country.set_ocha_url('NOTEXIST')
        Country._countriesdata = None
        assert Country.get_iso3_from_iso2('AF') == 'AFG'

