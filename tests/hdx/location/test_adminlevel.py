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
    def config_parent(self):
        return load_yaml(join("tests", "fixtures", "adminlevelparent.yaml"))

    @pytest.fixture(scope="function")
    def url(self):
        return "https://raw.githubusercontent.com/OCHA-DAP/hdx-python-country/main/tests/fixtures/global_pcodes_adm_1_2.csv"

    @pytest.fixture(scope="function")
    def formats_url(self):
        return "https://raw.githubusercontent.com/OCHA-DAP/hdx-python-country/main/tests/fixtures/global_pcode_lengths.csv"

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
        assert adminone.use_parent is False
        assert adminone.pcode_to_iso3["YE30"] == "YEM"
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
        output = adminone.output_admin_name_mappings()
        assert len(output) == 62
        assert output[0] == "Nord-Ouest: North West (HT09)"
        assert output[31] == "Juba Dhexe: Middle Juba (SO27)"
        assert output[61] == "CU Niamey: Niamey (NER008)"

        output = adminone.output_admin_name_replacements()
        assert output == [
            " urban: ",
            "sud: south",
            "ouest: west",
            "est: east",
            "nord: north",
            "': ",
            "/:  ",
            ".:  ",
            " region: ",
            " oblast: ",
        ]

    def test_adminlevel_fuzzy(self, config):
        adminone = AdminLevel(config)
        adminone.setup_from_admin_info(config["admin_info"])
        assert adminone.get_pcode("YEM", "Al_Dhale'a", logname="test") == (
            "YE30",
            False,
        )
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
        assert adminone.get_pcode("SOM", "Bay", logname="test") == (
            "SO24",
            True,
        )
        output = adminone.output_matches()
        assert output == [
            "test - YEM: Matching (fuzzy) Al Dali to Ad Dali on map",
            "test - YEM: Matching (fuzzy) Al Dhale'e / الضالع to Ad Dali on map",
            "test - YEM: Matching (fuzzy) Al_Dhale'a to Ad Dali on map",
        ]

    def test_adminlevel_parent(self, config_parent):
        admintwo = AdminLevel(config_parent)
        admintwo.countries_fuzzy_try = None
        admintwo.setup_from_admin_info(config_parent["admin_info_with_parent"])
        assert admintwo.use_parent is True
        assert admintwo.pcode_to_parent["AF0101"] == "AF01"
        assert admintwo.get_pcode("AFG", "AF0101", logname="test") == (
            "AF0101",
            True,
        )
        assert admintwo.get_pcode(
            "AFG", "AF0101", parent="blah", logname="test"
        ) == ("AF0101", True)
        assert admintwo.get_pcode("AFG", "Kabul", logname="test") == (
            "AF0201",
            True,
        )
        assert admintwo.get_pcode(
            "AFG", "Kabul", parent="AF01", logname="test"
        ) == ("AF0101", True)
        assert admintwo.get_pcode(
            "AFG", "Kabul", parent="blah", logname="test"
        ) == (None, False)
        assert admintwo.get_pcode(
            "AFG", "Kabul", parent="AF02", logname="test"
        ) == ("AF0201", True)
        assert admintwo.get_pcode(
            "AFG", "Kabull", parent="AF01", logname="test"
        ) == ("AF0101", False)
        assert admintwo.get_pcode(
            "AFG", "Kabull", parent="blah", logname="test"
        ) == (None, False)
        assert admintwo.get_pcode(
            "AFG", "Kabull", parent="AF02", logname="test"
        ) == ("AF0201", False)
        assert admintwo.get_pcode(
            "ABC", "Kabull", parent="AF02", logname="test"
        ) == (None, False)

        output = admintwo.output_admin_name_mappings()
        assert output == [
            "MyMapping: Charikar (AF0301)",
            "AFG|MyMapping2: Maydan Shahr (AF0401)",
            "AF05|MyMapping3: Pul-e-Alam (AF0501)",
        ]
        assert admintwo.get_pcode("AFG", "MyMapping", logname="test") == (
            "AF0301",
            True,
        )
        assert admintwo.get_pcode(
            "AFG", "MyMapping", parent="AF03", logname="test"
        ) == ("AF0301", True)
        assert admintwo.get_pcode(
            "AFG", "MyMapping", parent="AF04", logname="test"
        ) == (None, False)

        assert admintwo.get_pcode("AFG", "MyMapping2", logname="test") == (
            "AF0401",
            True,
        )
        assert admintwo.get_pcode(
            "AFG", "MyMapping2", parent="AF04", logname="test"
        ) == ("AF0401", True)
        assert admintwo.get_pcode(
            "AFG", "MyMapping2", parent="AF05", logname="test"
        ) == (None, False)

        assert admintwo.get_pcode("AFG", "MyMapping3", logname="test") == (
            None,
            False,
        )
        assert admintwo.get_pcode(
            "AFG", "MyMapping3", parent="AF05", logname="test"
        ) == ("AF0501", True)
        assert admintwo.get_pcode(
            "AFG", "MyMapping3", parent="AF04", logname="test"
        ) == (None, False)

        output = admintwo.output_admin_name_replacements()
        assert output == [" city: "]
        assert admintwo.get_pcode(
            "COD", "Mbanza-Ngungu city", logname="test"
        ) == ("CD2013", False)
        assert admintwo.get_pcode(
            "COD", "Mbanza-Ngungu city", parent="CD20", logname="test"
        ) == ("CD2013", False)
        assert admintwo.get_pcode(
            "COD", "Mbanza-Ngungu city", parent="CD19", logname="test"
        ) == (None, False)
        assert admintwo.get_pcode("COD", "Kenge city", logname="test") == (
            "CD3102",
            False,
        )
        assert admintwo.get_pcode("MWI", "Blantyre city", logname="test") == (
            "MW305",
            False,
        )

        admintwo.admin_name_replacements = config_parent[
            "alt1_admin_name_replacements"
        ]
        output = admintwo.output_admin_name_replacements()
        assert output == ["COD| city: "]
        assert admintwo.get_pcode(
            "COD", "Mbanza-Ngungu city", logname="test"
        ) == ("CD2013", False)
        assert admintwo.get_pcode(
            "COD", "Mbanza-Ngungu city", parent="CD20", logname="test"
        ) == ("CD2013", False)
        assert admintwo.get_pcode(
            "COD", "Mbanza-Ngungu city", parent="CD19", logname="test"
        ) == (None, False)
        assert admintwo.get_pcode("COD", "Kenge city", logname="test") == (
            "CD3102",
            False,
        )
        assert admintwo.get_pcode(
            "COD", "Kenge city", parent="CD31", logname="test"
        ) == ("CD3102", False)
        assert admintwo.get_pcode("MWI", "Blantyre city", logname="test") == (
            None,
            False,
        )
        assert admintwo.get_pcode(
            "MWI", "Blantyre city", parent="MW3", logname="test"
        ) == (None, False)

        admintwo.admin_name_replacements = config_parent[
            "alt2_admin_name_replacements"
        ]
        output = admintwo.output_admin_name_replacements()
        assert output == ["CD20| city: "]
        assert admintwo.get_pcode(
            "COD", "Mbanza-Ngungu city", logname="test"
        ) == (None, False)
        assert admintwo.get_pcode(
            "COD", "Mbanza-Ngungu city", parent="CD20", logname="test"
        ) == ("CD2013", False)
        assert admintwo.get_pcode(
            "COD", "Mbanza-Ngungu city", parent="CD19", logname="test"
        ) == (None, False)
        assert admintwo.get_pcode("COD", "Kenge city", logname="test") == (
            None,
            False,
        )
        assert admintwo.get_pcode(
            "COD", "Kenge city", parent="CD31", logname="test"
        ) == (None, False)
        assert admintwo.get_pcode("MWI", "Blantyre city", logname="test") == (
            None,
            False,
        )
        assert admintwo.get_pcode(
            "MWI", "Blantyre city", parent="MW3", logname="test"
        ) == (None, False)

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
        assert len(adminone.get_pcode_list()) == 2509
        assert adminone.get_pcode_length("YEM") == 4
        assert adminone.get_pcode("YEM", "YE30", logname="test") == (
            "YE30",
            True,
        )
        assert adminone.get_pcode(
            "YEM", "YE30", parent="YEM", logname="test"
        ) == (
            "YE30",
            True,
        )
        # Exact match of p-code so doesn't need parent
        assert adminone.get_pcode(
            "YEM", "YE30", parent="Blah1", logname="test"
        ) == (
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
            "NE004",
            True,
        )
        assert adminone.get_pcode("NER", "NE04", logname="test") == (
            "NE004",
            True,
        )
        assert adminone.get_pcode("NER", "NE004", logname="test") == (
            "NE004",
            True,
        )
        assert adminone.get_pcode("ABC", "NE004", logname="test") == (
            "NE004",
            True,
        )
        assert adminone.get_pcode("ABC", "NER004", logname="test") == (
            None,
            True,
        )
        assert adminone.get_pcode("ABC", "BLAH", logname="test") == (
            None,
            False,
        )
        config["countries_fuzzy_try"].append("ABC")
        assert adminone.get_pcode("ABC", "NER004", logname="test") == (
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
        assert adminone.get_pcode(
            "YEM", "Ad Dal", parent="YEM", logname="test"
        ) == (
            "YE30",
            False,
        )
        # Invalid parent means fuzzy matching won't match
        assert adminone.get_pcode(
            "YEM", "Ad Dal", parent="Blah2", logname="test"
        ) == (
            None,
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
            "test - NER: Matching (pcode length conversion) NE004 to Maradi on map",
            "test - NGA: Matching (pcode length conversion) NG015 to Federal Capital Territory on map",
            "test - UKR: Matching (substring) Chernihiv Oblast to Chernihivska on map",
            "test - YEM: Matching (substring) Ad Dal to Ad Dali' on map",
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
            "test - YEM: Could not find Blah2 in map names!",
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
        assert admintwo.pcode_to_parent["YE3001"] == "YE30"
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
        assert admintwo.get_pcode(
            "YEM", "YEM3001", parent="Blah", logname="test"
        ) == (
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
        assert admintwo.get_pcode(
            "NER", "NE00409", parent="blah", logname="test"
        ) == (
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
        # we don't use the parent because it could have a pcode length issue
        # itself
        assert admintwo.get_pcode(
            "NER", "NE00409", parent="blah", logname="test"
        ) == (
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
