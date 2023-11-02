"""location Tests"""
from os.path import join

import pytest
from hxl.input import HXLIOException

from hdx.location.adminlevel import AdminLevel
from hdx.utilities.loader import load_yaml


class TestAdminLevel:
    @pytest.fixture(scope="function")
    def config(self):
        return load_yaml(join("tests", "fixtures", "adminlevel.yaml"))

    @pytest.fixture(scope="function")
    def url(self):
        return "https://raw.githubusercontent.com/OCHA-DAP/hdx-python-country/main/tests/fixtures/global_pcodes_adm_1_2.csv"

    @pytest.fixture(scope="function")
    def formats_url(self):
        return "https://raw.githubusercontent.com/OCHA-DAP/hdx-python-country/pcode_formats/tests/fixtures/global_pcode_lengths.csv"

    def test_adminlevel(self, config):
        adminone = AdminLevel(config)
        adminone.setup_from_admin_info(
            config["admin_info"], countryiso3s=("yem",)
        )
        assert len(adminone.get_pcode_list()) == 22
        adminone = AdminLevel(config)
        adminone.setup_from_admin_info(config["admin_info"])
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
            True,
        )
        assert adminone.get_pcode("ABC", "BLAH", logname="test") == (
            None,
            False,
        )
        config["countries_fuzzy_try"].append("ABC")
        assert adminone.get_pcode("ABC", "NE004", logname="test") == (
            None,
            True,
        )
        assert adminone.get_pcode("ABC", "BLAH", logname="test") == (
            None,
            False,
        )
        assert adminone.get_pcode("XYZ", "XYZ123", logname="test") == (
            None,
            True,
        )
        assert adminone.get_pcode("XYZ", "BLAH", logname="test") == (
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
        assert adminone.get_pcode(
            "UKR",
            "Chernihiv Oblast",
            fuzzy_match=False,
            logname="test",
        ) == (
            None,
            True,
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
        adminone.setup_from_admin_info(config["admin_info"])
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

    def test_adminlevel_with_url(self, config, url):
        adminone = AdminLevel(config)
        with pytest.raises(HXLIOException):
            adminone.setup_from_url("fake_url")
        AdminLevel.set_default_admin_url()
        assert AdminLevel._admin_url == AdminLevel._admin_url_default
        AdminLevel.set_default_admin_url(url)
        assert AdminLevel._admin_url == url
        adminone.setup_from_url(countryiso3s=("YEM",))
        assert len(adminone.get_pcode_list()) == 22
        adminone = AdminLevel(config)
        adminone.setup_from_url()
        assert adminone.get_admin_level("YEM") == 1
        assert len(adminone.get_pcode_list()) == 2552
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
            True,
        )
        assert adminone.get_pcode("ABC", "BLAH", logname="test") == (
            None,
            False,
        )
        config["countries_fuzzy_try"].append("ABC")
        assert adminone.get_pcode("ABC", "NE004", logname="test") == (
            None,
            True,
        )
        assert adminone.get_pcode("ABC", "BLAH", logname="test") == (
            None,
            False,
        )
        assert adminone.get_pcode("XYZ", "XYZ123", logname="test") == (
            None,
            True,
        )
        assert adminone.get_pcode("XYZ", "BLAH", logname="test") == (
            None,
            False,
        )
        assert adminone.get_pcode("NER", "ABCDEFGH", logname="test") == (
            None,
            False,
        )
        assert adminone.get_pcode("YEM", "Ad Dali", logname="test") == (
            "YE30",
            False,
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
            "test - YEM: Matching (substring) Ad Dal to Ad Dali' on map",
            "test - YEM: Matching (substring) Ad Dali to Ad Dali' on map",
            "test - YEM: Matching (pcode length conversion) YE30 to Ad Dali' on map",
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

    def test_adminlevel_pcode_formats(self, config, url, formats_url):
        adminone = AdminLevel(config)
        adminone.setup_from_url(admin_url=url)
        adminone.load_pcode_formats(formats_url=formats_url)
        assert adminone.convert_admin_pcode_length("YEM", "YEME123") is None
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
            True,
        )

        admintwo = AdminLevel(config, admin_level=2)
        admintwo.setup_from_url(admin_url=url)
        assert admintwo.get_pcode("YEM", "YE03001", logname="test") == (
            None,
            True,
        )

        admintwo.load_pcode_formats(formats_url=formats_url)
        assert admintwo.get_pcode("YEM", "YE3001", logname="test") == (
            "YE3001",
            True,
        )
        assert admintwo.get_pcode("YEM", "YEM3001", logname="test") == (
            "YE3001",
            True,
        )
        assert admintwo.get_pcode("YEM", "YEM03001", logname="test") == (
            "YE3001",
            True,
        )
        assert admintwo.get_pcode("YEM", "YE301", logname="test") == (
            "YE3001",
            True,
        )
        assert admintwo.get_pcode("YEM", "YEM30001", logname="test") == (
            "YE3001",
            True,
        )
        assert admintwo.get_pcode("YEM", "YEM030001", logname="test") == (
            "YE3001",
            True,
        )
        assert admintwo.get_pcode("NGA", "NG015001", logname="test") == (
            "NG015001",
            True,
        )
        assert admintwo.get_pcode("NGA", "NG15001", logname="test") == (
            "NG015001",
            True,
        )
        assert admintwo.get_pcode("NGA", "NGA015001", logname="test") == (
            "NG015001",
            True,
        )
        assert admintwo.get_pcode("NGA", "NG1501", logname="test") == (
            "NG015001",
            True,
        )
        assert admintwo.get_pcode("NGA", "NG3614", logname="test") == (
            "NG036014",
            True,
        )
        # Algorithm inserts 0 to make NG001501 and hence fails (NG001 is in any
        # case a valid admin 1)
        assert admintwo.get_pcode("NGA", "NG01501", logname="test") == (
            None,
            True,
        )
        # Algorithm can only insert one zero per admin level right now
        assert admintwo.get_pcode("NGA", "NG0151", logname="test") == (
            None,
            True,
        )
        assert admintwo.get_pcode("NGA", "NG151", logname="test") == (
            None,
            True,
        )
        assert admintwo.get_pcode("NER", "NER004009", logname="test") == (
            "NER004009",
            True,
        )
        assert admintwo.get_pcode("NER", "NE04009", logname="test") == (
            "NER004009",
            True,
        )
        # Algorithm inserts 0 to make NER000409 and hence fails (it has no
        # knowledge that NER000 is an invalid admin 1)
        assert admintwo.get_pcode("NER", "NE00409", logname="test") == (
            None,
            True,
        )

        assert admintwo.get_pcode("DZA", "DZ009009", logname="test") == (
            "DZ009009",
            True,
        )
        assert admintwo.get_pcode("DZA", "DZ0090009", logname="test") == (
            "DZ009009",
            True,
        )

        assert admintwo.get_pcode("COL", "CO08849", logname="test") == (
            "CO08849",
            True,
        )
        # Algorithm removes 0 to make CO80849 and hence fails (it has no
        # knowledge that CO80 is an invalid admin 1)
        assert admintwo.get_pcode("COL", "CO080849", logname="test") == (
            None,
            True,
        )

        admintwo.set_parent_admins_from_adminlevels([adminone])
        # The lookup in admin1 reveals that adding a 0 prefix to the admin1
        # is not a valid admin1 (NER000) so the algorithm tries adding
        # the 0 prefix at the admin2 level instead and hence succeeds
        assert admintwo.get_pcode("NER", "NE00409", logname="test") == (
            "NER004009",
            True,
        )
        # The lookup in admin1 reveals that removing the 0 prefix from the
        # admin1 is not a valid admin1 (CO80849) so the algorithm tries
        # removing the 0 prefix at the admin2 level instead and hence succeeds
        assert admintwo.get_pcode("COL", "CO080849", logname="test") == (
            "CO08849",
            True,
        )

        admintwo.set_parent_admins([adminone.pcodes])
        assert admintwo.get_pcode("YEM", "YEM03001", logname="test") == (
            "YE3001",
            True,
        )
        assert admintwo.get_pcode("NGA", "NG1501", logname="test") == (
            "NG015001",
            True,
        )
