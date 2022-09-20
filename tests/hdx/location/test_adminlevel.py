"""location Tests"""
from os.path import join

import pytest
from hdx.utilities.loader import load_yaml

from hdx.location.adminlevel import AdminLevel


class TestAdminLevel:
    @pytest.fixture(scope="function")
    def config(self):
        return load_yaml(join("tests", "fixtures", "adminlevel.yml"))

    def test_adminlevel(self, config):
        adminone = AdminLevel(config)
        assert adminone.get_admin_level("YEM") == 1
        assert len(adminone.get_pcode_list()) == 433
        assert adminone.get_pcode_length("YEM") == 4
        assert adminone.get_pcode("YEM", "YE30", logname="test") == (
            "YE30",
            True,
        )
        assert adminone.get_pcode("YEM", "YEM30", logname="test") == (
            "YE30",
            True,
        )
        assert adminone.get_pcode("YEM", "YEM030", logname="test") == (
            "YE30",
            True,
        )
        assert adminone.get_pcode("NGA", "NG015", logname="test") == (
            "NG015",
            True,
        )
        assert adminone.get_pcode("NGA", "NG15", logname="test") == (
            "NG015",
            True,
        )
        assert adminone.get_pcode("NGA", "NGA015", logname="test") == (
            "NG015",
            True,
        )
        assert adminone.get_pcode("NER", "NER004", logname="test") == (
            "NER004",
            True,
        )
        assert adminone.get_pcode("NER", "NE04", logname="test") == (
            "NER004",
            True,
        )
        assert adminone.get_pcode("NER", "NE004", logname="test") == (
            "NER004",
            True,
        )
        assert adminone.get_pcode("ABC", "NE004", logname="test") == (
            None,
            False,
        )
        config["countries_fuzzy_try"].append("ABC")
        assert adminone.get_pcode("ABC", "NE004", logname="test") == (
            None,
            False,
        )
        assert adminone.get_pcode("XYZ", "XYZ123", logname="test") == (
            None,
            False,
        )
        assert adminone.get_pcode("NER", "ABCDEFGH", logname="test") == (
            None,
            False,
        )
        assert adminone.get_pcode("YEM", "Ad Dali", logname="test") == (
            "YE30",
            True,
        )
        assert adminone.get_pcode("YEM", "Ad Dal", logname="test") == (
            "YE30",
            False,
        )
        assert adminone.get_pcode("YEM", "nord", logname="test") == (
            None,
            False,
        )
        assert adminone.get_pcode("NGA", "FCT (Abuja)", logname="test") == (
            "NG015",
            True,
        )
        assert adminone.get_pcode(
            "UKR", "Chernihiv Oblast", logname="test"
        ) == (
            "UA74",
            False,
        )
        assert adminone.get_pcode("ZWE", "ABCDEFGH", logname="test") == (
            None,
            False,
        )
        output = adminone.output_matches()
        assert output == [
            "test - NER: Matching (pcode length conversion) NER004 to Maradi on map",
            "test - NGA: Matching (pcode length conversion) NG015 to Federal Capital Territory on map",
            "test - UKR: Matching (substring) Chernihiv Oblast to Chernihivska on map",
            "test - YEM: Matching (substring) Ad Dal to Ad Dali on map",
            "test - YEM: Matching (pcode length conversion) YE30 to Ad Dali on map",
        ]
        output = adminone.output_ignored()
        assert output == [
            "test - Ignored ABC!",
            "test - Ignored XYZ!",
            "test - YEM: Ignored nord!",
            "test - Ignored ZWE!",
        ]
        output = adminone.output_errors()
        assert output == [
            "test - Could not find ABC in map names!",
            "test - NER: Could not find ABCDEFGH in map names!",
        ]

    def test_adminlevel_fuzzy(self, config):
        adminone = AdminLevel(config)
        assert adminone.get_pcode("YEM", "Al Dali", logname="test") == (
            "YE30",
            False,
        )
        assert adminone.get_pcode(
            "YEM", "Al Dhale'e / الضالع", logname="test"
        ) == (
            "YE30",
            False,
        )
        output = adminone.output_matches()
        assert output == [
            "test - YEM: Matching (fuzzy) Al Dali to Ad Dali on map",
            "test - YEM: Matching (fuzzy) Al Dhale'e / الضالع to Ad Dali on map",
        ]
