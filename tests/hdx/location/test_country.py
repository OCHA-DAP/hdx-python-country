"""location Tests"""

import pytest
from hdx.utilities.downloader import Download
from hdx.utilities.path import script_dir_plus_file

from hdx.location.country import Country


class LocationError(Exception):
    pass


class TestCountry:
    def clear_data(self):
        Country._countriesdata = None
        Country.set_use_live_default(False)
        Country.set_ocha_url()
        Country.set_ocha_path()

    def setup_unofficial_date(self):
        self.clear_data()
        Country.set_include_unofficial_default(True)
        Country.countriesdata()

    @pytest.fixture(scope="function", autouse=True)
    def setup(self):
        # Clean up Country class before each test
        self.clear_data()
        Country.set_include_unofficial_default(False)
        Country.countriesdata(
            country_name_overrides={"PSE": "oPt"},
            country_name_mappings={"Congo DR": "COD"},
        )

    def test_get_country_name_from_iso3(self):
        assert Country.get_country_name_from_iso3("jpn") == "Japan"
        assert Country.get_country_name_from_iso3("awe") is None
        assert Country.get_country_name_from_iso3("Pol") == "Poland"
        assert Country.get_country_name_from_iso3("SGP") == "Singapore"
        assert (
            Country.get_country_name_from_iso3("SGP", formal=True)
            == "the Republic of Singapore"
        )
        assert Country.get_country_name_from_iso3("uy") is None
        with pytest.raises(LocationError):
            Country.get_country_name_from_iso3("uy", exception=LocationError)
        assert Country.get_country_name_from_iso3("uy") is None
        assert (
            Country.get_country_name_from_iso3("VeN")
            == "Venezuela (Bolivarian Republic of)"
        )
        assert (
            Country.get_country_name_from_iso3("vEn", formal=True)
            == "the Bolivarian Republic of Venezuela"
        )
        assert Country.get_country_name_from_iso3("TWN") == "Taiwan (Province of China)"
        assert (
            Country.get_country_name_from_iso3("TWN", formal=True)
            == "Taiwan (Province of China)"
        )
        assert Country.get_country_name_from_iso3("PSE") == "oPt"
        with pytest.raises(LocationError):
            Country.get_iso2_from_iso3("CHI", exception=LocationError)
        self.setup_unofficial_date()
        assert Country.get_country_name_from_iso3("CHI") == "Channel Islands"

    def test_get_iso2_from_iso3(self):
        assert Country.get_iso2_from_iso3("jpn") == "JP"
        assert Country.get_iso2_from_iso3("abc") is None
        with pytest.raises(LocationError):
            Country.get_iso2_from_iso3("abc", exception=LocationError)

    def test_get_iso3_from_iso2(self):
        assert Country.get_iso3_from_iso2("jp") == "JPN"
        assert Country.get_iso3_from_iso2("ab") is None
        with pytest.raises(LocationError):
            Country.get_iso3_from_iso2("ab", exception=LocationError)

    def test_get_country_info_from_iso3(self):
        assert Country.get_country_info_from_iso3("bih") == {
            "Admin Level": "0",
            "Appears in DGACM list": "Y",
            "Appears in UNTERM list": "Y",
            "Arabic Short": "البوسنة والهرسك",
            "Chinese Short": "波斯尼亚和黑塞哥维那",
            "Concatenation": "28 - Bosnia and Herzegovina",
            "Currency": "BAM",
            "DGACM Alt Term": None,
            "Deprecated": "N",
            "English Formal": "Bosnia and Herzegovina",
            "English Short": "Bosnia and Herzegovina",
            "French Short": "Bosnie-Herzégovine",
            "HPC Tools API ID": "28",
            "HPC Tools Alt Term": None,
            "Has HRP": None,
            "ID": "28",
            "ISO 3166-1 Alpha 2-Codes": "BA",
            "ISO 3166-1 Alpha 3-Codes": "BIH",
            "ISO Alt Term": None,
            "In GHO": None,
            "Independent": "Y",
            "Intermediate Region Code": None,
            "Intermediate Region Name": None,
            "Latitude": "44.16506495",
            "Longitude": "17.79105724",
            "M49 Arabic": "البوسنة والهرسك",
            "M49 Chinese": "波斯尼亚和黑塞哥维那",
            "M49 English": "Bosnia and Herzegovina",
            "M49 French": "Bosnie-Herzégovine",
            "M49 Russian": "Босния и Герцеговина",
            "M49 Spanish": "Bosnia y Herzegovina",
            "Preferred Term": "Bosnia and Herzegovina",
            "RW API Alt Term": None,
            "RW ID": "40",
            "RW Short Name": None,
            "Reference Period Start": "1993-01-01",
            "Regex": "herzegovina|bosnia",
            "Region Code": "150",
            "Region Name": "Europe",
            "Russian Short": "Босния и Герцеговина",
            "Spanish Short": "Bosnia y Herzegovina",
            "Sub-region Code": "39",
            "Sub-region Name": "Southern Europe",
            "World Bank Income Level": "Upper middle",
            "m49 numerical code": "70",
            "x Alpha2 codes": None,
            "x Alpha3 codes": None,
        }
        assert Country.get_country_info_from_iso3("PSE") == {
            "Admin Level": "0",
            "Appears in DGACM list": None,
            "Appears in UNTERM list": "Y",
            "Arabic Short": "دولة فلسطين",
            "Chinese Short": "巴勒斯坦国",
            "Concatenation": "170 - State of Palestine",
            "Currency": "ILS",
            "DGACM Alt Term": None,
            "Deprecated": "N",
            "English Formal": "the State of Palestine",
            "English Short": "State of Palestine",
            "French Short": "État de Palestine",
            "HPC Tools API ID": "171",
            "HPC Tools Alt Term": "occupied Palestinian territory",
            "Has HRP": None,
            "ID": "170",
            "ISO 3166-1 Alpha 2-Codes": "PS",
            "ISO 3166-1 Alpha 3-Codes": "PSE",
            "ISO Alt Term": "Palestine, State of",
            "In GHO": "Y",
            "Independent": "Y",
            "Intermediate Region Code": None,
            "Intermediate Region Name": None,
            "Latitude": "31.99084142",
            "Longitude": "35.30744047",
            "M49 Arabic": "دولة فلسطين",
            "M49 Chinese": "巴勒斯坦国",
            "M49 English": "State of Palestine",
            "M49 French": "État de Palestine",
            "M49 Russian": "Государство Палестина",
            "M49 Spanish": "Estado de Palestina",
            "Name Override": "oPt",
            "Preferred Term": "State of Palestine",
            "RW API Alt Term": "occupied Palestinian territory",
            "RW ID": "180",
            "RW Short Name": "oPt",
            "Reference Period Start": "2013-02-06",
            "Regex": "palestin|\\bgaza|west.?bank",
            "Region Code": "142",
            "Region Name": "Asia",
            "Russian Short": "Государство Палестина",
            "Spanish Short": "Estado de Palestina",
            "Sub-region Code": "145",
            "Sub-region Name": "Western Asia",
            "World Bank Income Level": "Upper middle",
            "m49 numerical code": "275",
            "x Alpha2 codes": None,
            "x Alpha3 codes": None,
        }
        with pytest.raises(LocationError):
            Country.get_country_name_from_iso2("AZO", exception=LocationError)
        self.setup_unofficial_date()
        assert Country.get_country_info_from_iso3("AZO") == {
            "Admin Level": None,
            "Appears in DGACM list": None,
            "Appears in UNTERM list": None,
            "Arabic Short": None,
            "Chinese Short": None,
            "Concatenation": "249 - Azores Islands (Portugal)",
            "Currency": "EUR",
            "DGACM Alt Term": None,
            "Deprecated": "N",
            "English Formal": None,
            "English Short": "Azores Islands",
            "French Short": None,
            "HPC Tools API ID": None,
            "HPC Tools Alt Term": None,
            "Has HRP": None,
            "ID": "249",
            "ISO 3166-1 Alpha 2-Codes": None,
            "ISO 3166-1 Alpha 3-Codes": None,
            "ISO Alt Term": None,
            "In GHO": None,
            "Independent": "N",
            "Intermediate Region Code": None,
            "Intermediate Region Name": None,
            "Latitude": "38.72708329",
            "Longitude": "-27.26017212",
            "M49 Arabic": None,
            "M49 Chinese": None,
            "M49 English": None,
            "M49 French": None,
            "M49 Russian": None,
            "M49 Spanish": None,
            "Preferred Term": "Azores Islands (Portugal)",
            "RW API Alt Term": None,
            "RW ID": "28",
            "RW Short Name": None,
            "Reference Period Start": "1974-01-01",
            "Regex": "azores",
            "Region Code": "150",
            "Region Name": "Europe",
            "Russian Short": None,
            "Spanish Short": None,
            "Sub-region Code": "39",
            "Sub-region Name": "Southern Europe",
            "World Bank Income Level": None,
            "m49 numerical code": None,
            "x Alpha2 codes": None,
            "x Alpha3 codes": "AZO",
        }

    def test_get_currency_from_iso3(self):
        assert Country.get_currency_from_iso3("jpn") == "JPY"
        assert Country.get_currency_from_iso3("abc") is None
        with pytest.raises(LocationError):
            Country.get_currency_from_iso3("abc", exception=LocationError)

    def test_get_country_info_from_iso2(self):
        assert Country.get_country_info_from_iso2("jp") == {
            "Admin Level": "0",
            "Appears in DGACM list": "Y",
            "Appears in UNTERM list": "Y",
            "Arabic Short": "اليابان",
            "Chinese Short": "日本",
            "Concatenation": "112 - Japan",
            "Currency": "JPY",
            "DGACM Alt Term": None,
            "Deprecated": "N",
            "English Formal": "Japan",
            "English Short": "Japan",
            "French Short": "Japon",
            "HPC Tools API ID": "112",
            "HPC Tools Alt Term": None,
            "Has HRP": None,
            "ID": "112",
            "ISO 3166-1 Alpha 2-Codes": "JP",
            "ISO 3166-1 Alpha 3-Codes": "JPN",
            "ISO Alt Term": None,
            "In GHO": None,
            "Independent": "Y",
            "Intermediate Region Code": None,
            "Intermediate Region Name": None,
            "Latitude": "37.63209801",
            "Longitude": "138.0812256",
            "M49 Arabic": "اليابان",
            "M49 Chinese": "日本",
            "M49 English": "Japan",
            "M49 French": "Japon",
            "M49 Russian": "Япония",
            "M49 Spanish": "Japón",
            "Preferred Term": "Japan",
            "RW API Alt Term": None,
            "RW ID": "128",
            "RW Short Name": None,
            "Reference Period Start": "1974-01-01",
            "Regex": "japan",
            "Region Code": "142",
            "Region Name": "Asia",
            "Russian Short": "Япония",
            "Spanish Short": "Japón",
            "Sub-region Code": "30",
            "Sub-region Name": "Eastern Asia",
            "World Bank Income Level": "High",
            "m49 numerical code": "392",
            "x Alpha2 codes": None,
            "x Alpha3 codes": None,
        }
        assert Country.get_country_info_from_iso2("ab") is None
        assert Country.get_country_info_from_iso2("TW") == {
            "Admin Level": "0",
            "Appears in DGACM list": None,
            "Appears in UNTERM list": None,
            "Arabic Short": None,
            "Chinese Short": None,
            "Concatenation": "218 - Taiwan (Province of China)",
            "Currency": "TWD",
            "DGACM Alt Term": None,
            "Deprecated": "N",
            "English Formal": None,
            "English Short": "Taiwan (Province of China)",
            "French Short": None,
            "HPC Tools API ID": "219",
            "HPC Tools Alt Term": "Taiwan, Province of China",
            "Has HRP": None,
            "ID": "218",
            "ISO 3166-1 Alpha 2-Codes": "TW",
            "ISO 3166-1 Alpha 3-Codes": "TWN",
            "ISO Alt Term": None,
            "In GHO": None,
            "Independent": "N",
            "Intermediate Region Code": None,
            "Intermediate Region Name": None,
            "Latitude": "23.74652012",
            "Longitude": "120.9621301",
            "M49 Arabic": None,
            "M49 Chinese": None,
            "M49 English": None,
            "M49 French": None,
            "M49 Russian": None,
            "M49 Spanish": None,
            "Preferred Term": "Taiwan (Province of China)",
            "RW API Alt Term": "China - Taiwan Province",
            "RW ID": "61",
            "RW Short Name": None,
            "Reference Period Start": "1974-01-01",
            "Regex": "taiwan|taipei|formosa|^(?!.*peo)(?=.*rep).*china",
            "Region Code": "142",
            "Region Name": "Asia",
            "Russian Short": None,
            "Spanish Short": None,
            "Sub-region Code": "30",
            "Sub-region Name": "Eastern Asia",
            "World Bank Income Level": "High",
            "m49 numerical code": "158",
            "x Alpha2 codes": None,
            "x Alpha3 codes": None,
        }

        assert Country.get_country_info_from_iso2("PS") == {
            "Admin Level": "0",
            "Appears in DGACM list": None,
            "Appears in UNTERM list": "Y",
            "Arabic Short": "دولة فلسطين",
            "Chinese Short": "巴勒斯坦国",
            "Concatenation": "170 - State of Palestine",
            "Currency": "ILS",
            "DGACM Alt Term": None,
            "Deprecated": "N",
            "English Formal": "the State of Palestine",
            "English Short": "State of Palestine",
            "French Short": "État de Palestine",
            "HPC Tools API ID": "171",
            "HPC Tools Alt Term": "occupied Palestinian territory",
            "Has HRP": None,
            "ID": "170",
            "ISO 3166-1 Alpha 2-Codes": "PS",
            "ISO 3166-1 Alpha 3-Codes": "PSE",
            "ISO Alt Term": "Palestine, State of",
            "In GHO": "Y",
            "Independent": "Y",
            "Intermediate Region Code": None,
            "Intermediate Region Name": None,
            "Latitude": "31.99084142",
            "Longitude": "35.30744047",
            "M49 Arabic": "دولة فلسطين",
            "M49 Chinese": "巴勒斯坦国",
            "M49 English": "State of Palestine",
            "M49 French": "État de Palestine",
            "M49 Russian": "Государство Палестина",
            "M49 Spanish": "Estado de Palestina",
            "Name Override": "oPt",
            "Preferred Term": "State of Palestine",
            "RW API Alt Term": "occupied Palestinian territory",
            "RW ID": "180",
            "RW Short Name": "oPt",
            "Reference Period Start": "2013-02-06",
            "Regex": "palestin|\\bgaza|west.?bank",
            "Region Code": "142",
            "Region Name": "Asia",
            "Russian Short": "Государство Палестина",
            "Spanish Short": "Estado de Palestina",
            "Sub-region Code": "145",
            "Sub-region Name": "Western Asia",
            "World Bank Income Level": "Upper middle",
            "m49 numerical code": "275",
            "x Alpha2 codes": None,
            "x Alpha3 codes": None,
        }
        with pytest.raises(LocationError):
            Country.get_country_info_from_iso2("XK", exception=LocationError)
        self.setup_unofficial_date()
        assert Country.get_country_info_from_iso2("XK") == {
            "Admin Level": None,
            "Appears in DGACM list": None,
            "Appears in UNTERM list": None,
            "Arabic Short": None,
            "Chinese Short": None,
            "Concatenation": "266 - Kosovo",
            "Currency": "EUR",
            "DGACM Alt Term": None,
            "Deprecated": "N",
            "English Formal": None,
            "English Short": "Kosovo",
            "French Short": None,
            "HPC Tools API ID": None,
            "HPC Tools Alt Term": None,
            "Has HRP": None,
            "ID": "266",
            "ISO 3166-1 Alpha 2-Codes": None,
            "ISO 3166-1 Alpha 3-Codes": None,
            "ISO Alt Term": None,
            "In GHO": None,
            "Independent": "N",
            "Intermediate Region Code": None,
            "Intermediate Region Name": None,
            "Latitude": "42.61901705",
            "Longitude": "20.90987836",
            "M49 Arabic": None,
            "M49 Chinese": None,
            "M49 English": None,
            "M49 French": None,
            "M49 Russian": None,
            "M49 Spanish": None,
            "Preferred Term": "Kosovo",
            "RW API Alt Term": None,
            "RW ID": None,
            "RW Short Name": None,
            "Reference Period Start": "1974-01-01",
            "Regex": "kosovo",
            "Region Code": "150",
            "Region Name": "Europe",
            "Russian Short": None,
            "Spanish Short": None,
            "Sub-region Code": "39",
            "Sub-region Name": "Southern Europe",
            "World Bank Income Level": None,
            "m49 numerical code": None,
            "x Alpha2 codes": "XK",
            "x Alpha3 codes": "XKX",
        }

        with pytest.raises(LocationError):
            Country.get_country_info_from_iso2("ab", exception=LocationError)

    def test_get_country_name_from_iso2(self):
        assert Country.get_country_name_from_iso2("jp") == "Japan"
        assert Country.get_country_name_from_iso2("ab") is None
        assert Country.get_country_name_from_iso2("Pl") == "Poland"
        assert Country.get_country_name_from_iso2("SG") == "Singapore"
        assert Country.get_country_name_from_iso2("SGP") is None
        with pytest.raises(LocationError):
            Country.get_country_name_from_iso2("SGP", exception=LocationError)
        assert (
            Country.get_country_name_from_iso2("VE")
            == "Venezuela (Bolivarian Republic of)"
        )
        assert (
            Country.get_country_name_from_iso2("VE", formal=True)
            == "the Bolivarian Republic of Venezuela"
        )
        assert Country.get_country_name_from_iso2("TW") == "Taiwan (Province of China)"
        assert Country.get_country_name_from_iso2("PS") == "oPt"
        with pytest.raises(LocationError):
            Country.get_country_name_from_iso2("AN", exception=LocationError)
        self.setup_unofficial_date()
        assert (
            Country.get_country_name_from_iso2("AN")
            == "Netherlands Antilles (The Netherlands)"
        )

    def test_get_currency_from_iso2(self):
        assert Country.get_currency_from_iso2("jp") == "JPY"
        assert Country.get_currency_from_iso2("ab") is None
        with pytest.raises(LocationError):
            Country.get_currency_from_iso2("ab", exception=LocationError)

    def test_get_m49_from_iso3(self):
        assert Country.get_m49_from_iso3("AFG") == 4
        assert Country.get_m49_from_iso3("WSM") == 882
        assert Country.get_m49_from_iso3("TWN") == 158
        assert Country.get_m49_from_iso3("ABC") is None
        with pytest.raises(LocationError):
            Country.get_m49_from_iso3("ABC", exception=LocationError)

    def test_get_iso3_from_m49(self):
        assert Country.get_iso3_from_m49(4) == "AFG"
        assert Country.get_iso3_from_m49(882) == "WSM"
        assert Country.get_iso3_from_m49(9999) is None
        with pytest.raises(LocationError):
            Country.get_iso3_from_m49(9999, exception=LocationError)

    def test_get_country_info_from_m49(self):
        assert Country.get_country_info_from_m49(4) == {
            "Admin Level": "0",
            "Appears in DGACM list": "Y",
            "Appears in UNTERM list": "Y",
            "Arabic Short": "أفغانستان",
            "Chinese Short": "阿富汗",
            "Concatenation": "1 - Afghanistan",
            "Currency": "AFN",
            "DGACM Alt Term": None,
            "Deprecated": "N",
            "English Formal": "the Islamic Republic of Afghanistan",
            "English Short": "Afghanistan",
            "French Short": "Afghanistan",
            "HPC Tools API ID": "1",
            "HPC Tools Alt Term": None,
            "Has HRP": "Y",
            "ID": "1",
            "ISO 3166-1 Alpha 2-Codes": "AF",
            "ISO 3166-1 Alpha 3-Codes": "AFG",
            "ISO Alt Term": None,
            "In GHO": "Y",
            "Independent": "Y",
            "Intermediate Region Code": None,
            "Intermediate Region Name": None,
            "Latitude": "33.83147477",
            "Longitude": "66.02621828",
            "M49 Arabic": "أفغانستان",
            "M49 Chinese": "阿富汗",
            "M49 English": "Afghanistan",
            "M49 French": "Afghanistan",
            "M49 Russian": "Афганистан",
            "M49 Spanish": "Afganistán",
            "Preferred Term": "Afghanistan",
            "RW API Alt Term": None,
            "RW ID": "13",
            "RW Short Name": None,
            "Reference Period Start": "2004-01-26",
            "Regex": "afghan",
            "Region Code": "142",
            "Region Name": "Asia",
            "Russian Short": "Афганистан",
            "Spanish Short": "Afganistán",
            "Sub-region Code": "34",
            "Sub-region Name": "Southern Asia",
            "World Bank Income Level": "Low",
            "m49 numerical code": "4",
            "x Alpha2 codes": None,
            "x Alpha3 codes": None,
        }
        assert Country.get_country_info_from_m49(882) == {
            "Admin Level": "0",
            "Appears in DGACM list": "Y",
            "Appears in UNTERM list": "Y",
            "Arabic Short": "ساموا",
            "Chinese Short": "萨摩亚",
            "Concatenation": "192 - Samoa",
            "Currency": "WST",
            "DGACM Alt Term": None,
            "Deprecated": "N",
            "English Formal": "the Independent State of Samoa",
            "English Short": "Samoa",
            "French Short": "Samoa",
            "HPC Tools API ID": "193",
            "HPC Tools Alt Term": None,
            "Has HRP": None,
            "ID": "192",
            "ISO 3166-1 Alpha 2-Codes": "WS",
            "ISO 3166-1 Alpha 3-Codes": "WSM",
            "ISO Alt Term": None,
            "In GHO": None,
            "Independent": "Y",
            "Intermediate Region Code": None,
            "Intermediate Region Name": None,
            "Latitude": "-13.16992041",
            "Longitude": "-173.5139768",
            "M49 Arabic": "ساموا",
            "M49 Chinese": "萨摩亚",
            "M49 English": "Samoa",
            "M49 French": "Samoa",
            "M49 Russian": "Самоа",
            "M49 Spanish": "Samoa",
            "Preferred Term": "Samoa",
            "RW API Alt Term": None,
            "RW ID": "204",
            "RW Short Name": None,
            "Reference Period Start": "1998-02-05",
            "Regex": "^(?!.*amer).*samoa",
            "Region Code": "9",
            "Region Name": "Oceania",
            "Russian Short": "Самоа",
            "Spanish Short": "Samoa",
            "Sub-region Code": "61",
            "Sub-region Name": "Polynesia",
            "World Bank Income Level": "Lower middle",
            "m49 numerical code": "882",
            "x Alpha2 codes": None,
            "x Alpha3 codes": None,
        }
        assert Country.get_country_info_from_m49(275) == {
            "Admin Level": "0",
            "Appears in DGACM list": None,
            "Appears in UNTERM list": "Y",
            "Arabic Short": "دولة فلسطين",
            "Chinese Short": "巴勒斯坦国",
            "Concatenation": "170 - State of Palestine",
            "Currency": "ILS",
            "DGACM Alt Term": None,
            "Deprecated": "N",
            "English Formal": "the State of Palestine",
            "English Short": "State of Palestine",
            "French Short": "État de Palestine",
            "HPC Tools API ID": "171",
            "HPC Tools Alt Term": "occupied Palestinian territory",
            "Has HRP": None,
            "ID": "170",
            "ISO 3166-1 Alpha 2-Codes": "PS",
            "ISO 3166-1 Alpha 3-Codes": "PSE",
            "ISO Alt Term": "Palestine, State of",
            "In GHO": "Y",
            "Independent": "Y",
            "Intermediate Region Code": None,
            "Intermediate Region Name": None,
            "Latitude": "31.99084142",
            "Longitude": "35.30744047",
            "M49 Arabic": "دولة فلسطين",
            "M49 Chinese": "巴勒斯坦国",
            "M49 English": "State of Palestine",
            "M49 French": "État de Palestine",
            "M49 Russian": "Государство Палестина",
            "M49 Spanish": "Estado de Palestina",
            "Name Override": "oPt",
            "Preferred Term": "State of Palestine",
            "RW API Alt Term": "occupied Palestinian territory",
            "RW ID": "180",
            "RW Short Name": "oPt",
            "Reference Period Start": "2013-02-06",
            "Regex": "palestin|\\bgaza|west.?bank",
            "Region Code": "142",
            "Region Name": "Asia",
            "Russian Short": "Государство Палестина",
            "Spanish Short": "Estado de Palestina",
            "Sub-region Code": "145",
            "Sub-region Name": "Western Asia",
            "World Bank Income Level": "Upper middle",
            "m49 numerical code": "275",
            "x Alpha2 codes": None,
            "x Alpha3 codes": None,
        }

        assert Country.get_country_info_from_m49(9999) is None
        with pytest.raises(LocationError):
            Country.get_country_info_from_m49(9999, exception=LocationError)

    def test_get_country_name_from_m49(self):
        assert Country.get_country_name_from_m49(4) == "Afghanistan"
        assert (
            Country.get_country_name_from_m49(158, formal=True)
            == "Taiwan (Province of China)"
        )
        assert Country.get_country_name_from_m49(882) == "Samoa"
        assert Country.get_country_name_from_m49(9999) is None
        assert Country.get_country_name_from_m49(275) == "oPt"
        with pytest.raises(LocationError):
            Country.get_country_name_from_m49(9999, exception=LocationError)

    def test_get_currency_from_m49(self):
        assert Country.get_currency_from_m49(4) == "AFN"
        assert Country.get_currency_from_m49(882) == "WST"
        assert Country.get_currency_from_m49(9999) is None
        with pytest.raises(LocationError):
            Country.get_currency_from_m49(9999, exception=LocationError)

    def test_expand_countryname_abbrevs(self):
        assert Country.expand_countryname_abbrevs("jpn") == ["JPN"]
        assert Country.expand_countryname_abbrevs("Haha Dem. Fed. Republic") == [
            "HAHA DEMOCRATIC FED. REPUBLIC",
            "HAHA DEMOCRATIC FEDERATION REPUBLIC",
            "HAHA DEMOCRATIC FEDERAL REPUBLIC",
            "HAHA DEMOCRATIC FEDERATED REPUBLIC",
        ]

    def test_simplify_countryname(self):
        # Test that we handle the empty string case
        assert Country.simplify_countryname("") == ("", [])

        # Test that country codes and arbitrary words return just the word but capitalised
        assert Country.simplify_countryname("jpn") == ("JPN", [])
        assert Country.simplify_countryname("test") == ("TEST", [])

        # Test simplified terms are removed, including abbreviations
        assert Country.simplify_countryname("United Rep. of Tanzania") == (
            "TANZANIA",
            ["UNITED", "REP", "OF"],
        )
        assert Country.simplify_countryname(
            "The former Yugoslav Republic of Macedonia"
        ) == ("MACEDONIA", ["THE", "FORMER", "YUGOSLAV", "REPUBLIC", "OF"])

        # Test different word orderings and bracketing are consistent
        assert Country.simplify_countryname("Micronesia (Federated States of)") == (
            "MICRONESIA",
            ["FEDERATED", "STATES", "OF"],
        )
        assert Country.simplify_countryname("Federated States of Micronesia") == (
            "MICRONESIA",
            ["FEDERATED", "STATES", "OF"],
        )
        assert Country.simplify_countryname("(Federated States of) Micronesia") == (
            "MICRONESIA",
            ["FEDERATED", "STATES", "OF"],
        )

        # Test that the simplified terms on their own are dropped and that we handle
        # the "no simplified term" case
        assert Country.simplify_countryname("Federated States") == (
            "",
            ["FEDERATED", "STATES"],
        )

        # Test that multi-word simplifications are dropped
        assert Country.simplify_countryname("French Part of Saint Martin") == (
            "MARTIN",
            ["FRENCH", "PART", "OF", "SAINT"],
        )
        assert Country.simplify_countryname("French Part of Saint-Martin") == (
            "MARTIN",
            ["FRENCH", "PART", "OF", "SAINT"],
        )
        # "French Part" is a simplification and so can't be the simplified term
        assert Country.simplify_countryname("French Part") == ("", ["FRENCH", "PART"])
        # But the words must be consecutive for multi-part terms,
        # so we don't drop "French" and "part" here
        assert Country.simplify_countryname("French and Part") == (
            "FRENCH",
            ["AND", "PART"],
        )

        # Test that we handle abbreviations with and without punctuation
        assert Country.simplify_countryname("Dem. Rep. of the Congo") == (
            "CONGO",
            ["DEM", "REP", "OF", "THE"],
        )
        assert Country.simplify_countryname("Dem Rep of the Congo") == (
            "CONGO",
            ["DEM", "REP", "OF", "THE"],
        )

        # Test that we handle the "Country, Specifics" comma format
        assert Country.simplify_countryname(
            "Korea, Democratic People's Republic of"
        ) == ("KOREA", ["DEMOCRATIC", "PEOPLE'S", "REPUBLIC", "OF"])
        assert Country.simplify_countryname(
            "Democratic People's Republic of Korea"
        ) == ("KOREA", ["DEMOCRATIC", "PEOPLE'S", "REPUBLIC", "OF"])

        # Test that we handle more bracketed formats
        assert Country.simplify_countryname("Korea (the Republic of))") == (
            "KOREA",
            ["THE", "REPUBLIC", "OF"],
        )
        # Regression test for bug #70 - partial brackets
        assert Country.simplify_countryname("Korea (the Republic of") == (
            "KOREA",
            ["THE", "REPUBLIC", "OF"],
        )

        # Test that we don't strip everything just because it's bracketed, even if the brackets
        # are surrounded by whitespace
        assert Country.simplify_countryname("(the Republic of Korea)") == (
            "KOREA",
            ["THE", "REPUBLIC", "OF"],
        )
        assert Country.simplify_countryname("   (the Republic of Korea)   ") == (
            "KOREA",
            ["THE", "REPUBLIC", "OF"],
        )

        # Test that we're actually stripping the brackets and that it's not all just been
        # simplified words that we'd drop anyway, even if they weren't in brackets
        assert Country.simplify_countryname("(Sometimes) Korea") == (
            "KOREA",
            ["SOMETIMES"],
        )

        # Regression test for bug #75 - apostrophes in simplified term
        assert Country.simplify_countryname("d'Ivoire Côte") == ("D'IVOIRE", ["CÔTE"])

        # Regression test for bug #77 - other punctuation in simplified term
        assert Country.simplify_countryname("Guinea-Bissau") == ("GUINEA", ["BISSAU"])

        # Test simplification of terms with apostrophes, and the non-apostrophe form
        assert Country.simplify_countryname("People's Republic of Bangladesh") == (
            "BANGLADESH",
            ["PEOPLE'S", "REPUBLIC", "OF"],
        )
        assert Country.simplify_countryname("Peoples Republic of Bangladesh") == (
            "BANGLADESH",
            ["PEOPLES", "REPUBLIC", "OF"],
        )
        # Known limitation with "smart quote" handling
        assert Country.simplify_countryname("People’s Republic of Bangladesh") == (
            "PEOPLE’S",
            ["REPUBLIC", "OF", "BANGLADESH"],
        )

        # Simplifying assumes that it isn't getting an address and simplifies to the first
        # part around commas, even if it isn't a country
        assert Country.simplify_countryname("Paris, France") == (
            "PARIS",
            ["FRANCE"],
        )

        # Some people supply strings that aren't countries
        # (often indirectly via `get_iso3_country_code_fuzzy()`)
        # Ensure the function doesn't error, even if the value is meaningless.
        assert Country.simplify_countryname("3.1 Global scores and ranking") == (
            "3",
            ["1", "GLOBAL", "SCORES", "AND", "RANKING"],
        )

    def test_get_iso3_country_code(self):
        assert Country.get_iso3_country_code("jpn") == "JPN"
        assert Country.get_iso3_country_code("Dem. Rep. of the Congo") == "COD"
        assert Country.get_iso3_country_code("Russian Fed.") == "RUS"
        assert Country.get_iso3_country_code("中国") == "CHN"
        assert Country.get_iso3_country_code("المملكة العربية السعودية") == "SAU"
        assert (
            Country.get_iso3_country_code("Micronesia (Federated States of)") == "FSM"
        )
        assert Country.get_iso3_country_code("Iran (Islamic Rep. of)") == "IRN"
        assert Country.get_iso3_country_code("United Rep. of Tanzania") == "TZA"
        assert Country.get_iso3_country_code("Syrian Arab Rep.") == "SYR"
        assert Country.get_iso3_country_code("Central African Rep.") == "CAF"
        assert Country.get_iso3_country_code("Rep. of Korea") == "KOR"
        assert Country.get_iso3_country_code("St. Pierre and Miquelon") == "SPM"
        assert Country.get_iso3_country_code("Christmas Isl.") == "CXR"
        assert Country.get_iso3_country_code("Cayman Isl.") == "CYM"
        assert Country.get_iso3_country_code("jp") == "JPN"
        assert Country.get_iso3_country_code("Taiwan (Province of China)") == "TWN"
        assert Country.get_iso3_country_code("Congo DR") == "COD"
        assert Country.get_iso3_country_code("oPt") == "PSE"
        assert (
            Country.get_iso3_country_code("Lao People's Democratic Republic") == "LAO"
        )
        assert Country.get_iso3_country_code_fuzzy("jpn") == ("JPN", True)
        assert Country.get_iso3_country_code_fuzzy("ZWE") == ("ZWE", True)
        assert Country.get_iso3_country_code_fuzzy("Vut") == ("VUT", True)
        assert Country.get_iso3_country_code_fuzzy("Congo DR") == ("COD", True)
        assert Country.get_iso3_country_code_fuzzy("laos") == ("LAO", False)
        assert Country.get_iso3_country_code("abc") is None
        assert Country.get_iso3_country_code("-") is None
        with pytest.raises(LocationError):
            Country.get_iso3_country_code("abc", exception=LocationError)
        assert Country.get_iso3_country_code_fuzzy("abc") == (None, False)
        assert Country.get_iso3_country_code_fuzzy("-") == (None, False)
        with pytest.raises(LocationError):
            Country.get_iso3_country_code_fuzzy("abcde", exception=LocationError)
        assert Country.get_iso3_country_code_fuzzy("United Kingdom") == (
            "GBR",
            True,
        )
        assert Country.get_iso3_country_code_fuzzy(
            "United Kingdom of Great Britain and Northern Ireland"
        ) == ("GBR", True)
        assert Country.get_iso3_country_code_fuzzy("united states") == (
            "USA",
            True,
        )
        assert Country.get_iso3_country_code_fuzzy("united states of america") == (
            "USA",
            True,
        )
        assert Country.get_iso3_country_code_fuzzy("america") == ("USA", False)
        assert Country.get_iso3_country_code("UZBEKISTAN") == "UZB"
        assert Country.get_iso3_country_code_fuzzy("UZBEKISTAN") == (
            "UZB",
            True,
        )
        assert Country.get_iso3_country_code("Sierra") is None
        assert Country.get_iso3_country_code_fuzzy("Sierra") == ("SLE", False)
        assert Country.get_iso3_country_code("Venezuela") == "VEN"
        assert Country.get_iso3_country_code_fuzzy("Venezuela") == (
            "VEN",
            True,
        )
        assert Country.get_iso3_country_code_fuzzy("Heard Isl.") == (
            "HMD",
            False,
        )
        assert Country.get_iso3_country_code_fuzzy("Falkland Isl.") == (
            "FLK",
            True,
        )
        assert Country.get_iso3_country_code_fuzzy("Czech Republic") == (
            "CZE",
            True,
        )
        assert Country.get_iso3_country_code_fuzzy("Czech Rep.") == (
            "CZE",
            True,
        )
        assert Country.get_iso3_country_code_fuzzy("Islamic Rep. of Iran") == (
            "IRN",
            False,
        )
        assert Country.get_iso3_country_code_fuzzy("Dem. Congo") == (
            "COD",
            False,
        )
        assert Country.get_iso3_country_code_fuzzy("Congo, Democratic Republic") == (
            "COD",
            False,
        )
        assert Country.get_iso3_country_code_fuzzy("Congo, Republic of") == (
            "COG",
            False,
        )
        assert Country.get_iso3_country_code_fuzzy("Republic of the Congo") == (
            "COG",
            False,
        )
        assert Country.get_iso3_country_code_fuzzy("Vietnam") == ("VNM", False)
        assert Country.get_iso3_country_code_fuzzy("South Korea") == (
            "KOR",
            False,
        )
        assert Country.get_iso3_country_code_fuzzy("Korea Republic") == (
            "KOR",
            False,
        )
        assert Country.get_iso3_country_code_fuzzy("Dem. Republic Korea") == (
            "PRK",
            False,
        )
        assert Country.get_iso3_country_code_fuzzy("North Korea") == (
            "PRK",
            False,
        )
        assert Country.get_iso3_country_code_fuzzy(
            "Serbia and Kosovo: S/RES/1244 (1999)"
        ) == ("SRB", False)
        assert Country.get_iso3_country_code_fuzzy("U.S. Virgin Islands") == (
            "VIR",
            True,
        )
        assert Country.get_iso3_country_code_fuzzy("U.K. Virgin Islands") == (
            "VGB",
            False,
        )
        assert Country.get_iso3_country_code_fuzzy("Taiwan") == ("TWN", False)
        assert Country.get_iso3_country_code_fuzzy("Taiwan*") == ("TWN", False)
        assert Country.get_iso3_country_code_fuzzy("Kosovo") == (None, False)
        assert Country.get_iso3_country_code_fuzzy("Kosovo*") == (None, False)
        assert Country.get_iso3_country_code_fuzzy("India") == ("IND", True)
        assert Country.get_iso3_country_code_fuzzy("India*") == ("IND", False)
        assert Country.get_iso3_country_code_fuzzy("*India") == ("IND", False)
        assert Country.get_iso3_country_code_fuzzy("Republic of India") == (
            "IND",
            False,
        )
        assert Country.get_iso3_country_code_fuzzy("Bassas Da India") == (
            None,
            False,
        )
        with pytest.raises(ValueError):
            Country.get_iso3_country_code("abc", exception=ValueError)
        with pytest.raises(ValueError):
            Country.get_iso3_country_code_fuzzy("abcde", exception=ValueError)
        self.setup_unofficial_date()
        assert Country.get_iso3_country_code_fuzzy("Kosovo") == ("XKX", True)
        assert Country.get_iso3_country_code_fuzzy("Kosovo*") == ("XKX", False)
        assert Country.get_iso3_country_code_fuzzy("d'Ivoire Côte") == ("CIV", False)

    def test_get_countries_in_region(self):
        assert Country.get_countries_in_region("Eastern Asia") == [
            "CHN",
            "HKG",
            "JPN",
            "KOR",
            "MAC",
            "MNG",
            "PRK",
            "TWN",
        ]
        assert len(Country.get_countries_in_region("Africa")) == 60
        assert Country.get_countries_in_region(13) == [
            "BLZ",
            "CRI",
            "GTM",
            "HND",
            "MEX",
            "NIC",
            "PAN",
            "SLV",
        ]
        assert Country.get_countries_in_region("Channel Islands") == [
            "GGY",
            "JEY",
        ]
        assert len(Country.get_countries_in_region("NOTEXIST")) == 0
        with pytest.raises(LocationError):
            Country.get_countries_in_region("NOTEXIST", exception=LocationError)

    def test_get_hrp_status_from_iso3(self):
        assert Country.get_hrp_status_from_iso3("jpn") is False
        assert Country.get_hrp_status_from_iso3("AFG") is True
        assert Country.get_hrp_status_from_iso3("Ago") is False
        assert Country.get_hrp_status_from_iso3("abc") is None

    def test_get_gho_status_from_iso3(self):
        assert Country.get_gho_status_from_iso3("jpn") is False
        assert Country.get_gho_status_from_iso3("AFG") is True
        assert Country.get_gho_status_from_iso3("Ago") is True
        assert Country.get_gho_status_from_iso3("abc") is None

    def test_use_live_default(self):
        Country.set_use_live_default(True)
        assert Country._use_live is True
        Country.set_use_live_default(False)
        assert Country._use_live is False
        # We should now be able to load from local data without setting use_live=False
        Country._countriesdata = None
        Country.set_ocha_path(
            script_dir_plus_file("Countries_UZB_Deleted.csv", TestCountry)
        )
        assert Country.get_iso3_country_code("UZBEKISTAN") is None
        Country.set_use_live_default(None)
        assert Country._use_live is True
        Country._countriesdata = None
        assert Country.get_iso3_country_code("UZBEKISTAN") == "UZB"
        Country._countriesdata = None

    def test_ocha_feed_file_working(self):
        with Download(user_agent="test") as downloader:
            _, countries = downloader.get_tabular_rows(
                script_dir_plus_file("Countries_UZB_Deleted.csv", TestCountry),
                dict_form=True,
            )
            Country.set_countriesdata(countries)
        assert Country.get_iso3_country_code("UZBEKISTAN") is None
        assert Country.get_iso3_country_code("south sudan") == "SSD"
        Country.set_ocha_url()
        Country._countriesdata = None
        assert Country.get_iso3_country_code("UZBEKISTAN", use_live=True) == "UZB"
        assert Country.get_iso3_country_code_fuzzy("Laos") == ("LAO", False)
        Country.set_ocha_url("NOTEXIST")
        Country._countriesdata = None
        assert Country.get_iso3_from_iso2("AF") == "AFG"

    def test_ocha_feed_local_file_working(self):
        Country._countriesdata = None
        Country.set_ocha_path(
            script_dir_plus_file("Countries_UZB_Deleted.csv", TestCountry)
        )
        assert Country.get_iso3_country_code("UZBEKISTAN", use_live=False) is None

        Country._countriesdata = None
        Country.set_ocha_path()
        assert Country.get_iso3_country_code("UZBEKISTAN", use_live=False) == "UZB"
