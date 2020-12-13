# -*- coding: UTF-8 -*-
"""location Tests"""
import sys
from os.path import join

import pytest
from hdx.utilities.loader import load_yaml

from hdx.location.adminone import AdminOne


class TestAdminOne:
    @pytest.fixture(scope='function')
    def config(self):
        return load_yaml(join('tests', 'fixtures', 'adminone.yml'))

    def test_adminone(self, config):
        adminone = AdminOne(config)
        assert adminone.get_pcode('YEM', 'YE30', scrapername='test') == ('YE30', True)
        assert adminone.get_pcode('YEM', 'YEM30', scrapername='test') == ('YE30', True)
        assert adminone.get_pcode('YEM', 'YEM030', scrapername='test') == ('YE30', True)
        assert adminone.get_pcode('NGA', 'NG015', scrapername='test') == ('NG015', True)
        assert adminone.get_pcode('NGA', 'NG15', scrapername='test') == ('NG015', True)
        assert adminone.get_pcode('NGA', 'NGA015', scrapername='test') == ('NG015', True)
        assert adminone.get_pcode('NER', 'NER004', scrapername='test') == ('NER004', True)
        assert adminone.get_pcode('NER', 'NE04', scrapername='test') == ('NER004', True)
        assert adminone.get_pcode('NER', 'NE004', scrapername='test') == ('NER004', True)
        assert adminone.get_pcode('ABC', 'NE004', scrapername='test') == (None, False)
        config['countries_fuzzy_try'].append('ABC')
        assert adminone.get_pcode('ABC', 'NE004', scrapername='test') == (None, False)
        assert adminone.get_pcode('XYZ', 'XYZ123', scrapername='test') == (None, False)
        assert adminone.get_pcode('NER', 'ABCDEFGH', scrapername='test') == (None, False)
        assert adminone.get_pcode('YEM', 'Ad Dali', scrapername='test') == ('YE30', True)
        assert adminone.get_pcode('YEM', 'Ad Dal', scrapername='test') == ('YE30', False)
        assert adminone.get_pcode('YEM', 'nord', scrapername='test') == (None, False)
        assert adminone.get_pcode('NGA', 'FCT (Abuja)', scrapername='test') == ('NG015', True)
        assert adminone.get_pcode('UKR', 'Chernihiv Oblast', scrapername='test') == ('UA74', False)
        assert adminone.get_pcode('ZWE', 'ABCDEFGH', scrapername='test') == (None, False)
        output = adminone.output_matches()
        assert output == ['test - NER: Matching (pcode length conversion) NER004 to Maradi on map',
                          'test - NGA: Matching (pcode length conversion) NG015 to Federal Capital Territory on map',
                          'test - UKR: Matching (substring) Chernihiv Oblast to Chernihivska on map',
                          'test - YEM: Matching (substring) Ad Dal to Ad Dali on map',
                          'test - YEM: Matching (pcode length conversion) YE30 to Ad Dali on map']
        output = adminone.output_ignored()
        assert output == ['test - Ignored ABC!',
                          'test - Ignored XYZ!',
                          'test - YEM: Ignored nord!',
                          'test - Ignored ZWE!']
        output = adminone.output_errors()
        assert output == ['test - Could not find ABC in map names!',
                          'test - NER: Could not find ABCDEFGH in map names!']

    @pytest.mark.skipif(sys.version_info[0] == 2, reason='Requires Python 3 or higher')
    def test_adminone_fuzzy(self, config):
        adminone = AdminOne(config)
        assert adminone.get_pcode('YEM', 'Al Dali', scrapername='test') == ('YE30', False)
        assert adminone.get_pcode('YEM', "Al Dhale'e / الضالع", scrapername='test') == ('YE30', False)
        output = adminone.output_matches()
        assert output == ['test - YEM: Matching (fuzzy) Al Dali to Ad Dali on map',
                          "test - YEM: Matching (fuzzy) Al Dhale'e / الضالع to Ad Dali on map"]
