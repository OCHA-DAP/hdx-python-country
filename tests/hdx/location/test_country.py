"""location Tests"""

import hxl
import pytest
from hxl import InputOptions

from hdx.location.country import Country
from hdx.utilities.path import script_dir_plus_file


class LocationError(Exception):
    pass


# Note that the Country class is set up in __init__.py
class TestCountry:
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
        assert (
            Country.get_country_name_from_iso3("TWN")
            == "Taiwan (Province of China)"
        )
        assert (
            Country.get_country_name_from_iso3("TWN", formal=True)
            == "Taiwan (Province of China)"
        )
        assert Country.get_country_name_from_iso3("PSE") == "oPt"

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
            "#country+alt+i_ar+name+v_unterm": "البوسنة والهرسك",
            "#country+alt+i_en+name+v_unterm": "Bosnia and Herzegovina",
            "#country+alt+i_es+name+v_unterm": "Bosnia y Herzegovina",
            "#country+alt+i_fr+name+v_unterm": "Bosnie-Herzégovine (la)",
            "#country+alt+i_ru+name+v_unterm": "Босния и Герцеговина",
            "#country+alt+i_zh+name+v_unterm": "波斯尼亚和黑塞哥维那",
            "#country+alt+name+v_dgacm": "",
            "#country+alt+name+v_fts": "",
            "#country+alt+name+v_hrinfo_country": "",
            "#country+alt+name+v_iso": "",
            "#country+alt+name+v_m49": "",
            "#country+alt+name+v_reliefweb": "",
            "#country+code+num+v_m49": "70",
            "#country+code+v_fts": "28",
            "#country+code+v_hrinfo_country": "208",
            "#country+code+v_iso2": "BA",
            "#country+code+v_iso3": "BIH",
            "#country+code+v_reliefweb": "40",
            "#country+formal+i_en+name+v_unterm": "Bosnia and Herzegovina",
            "#country+name+preferred": "Bosnia and Herzegovina",
            "#country+name+short+v_reliefweb": "",
            "#country+regex": "herzegovina|bosnia",
            "#currency+code": "BAM",
            "#date+start": "1993-01-01",
            "#geo+admin_level": "0",
            "#geo+lat": "44.16506495",
            "#geo+lon": "17.79105724",
            "#indicator+incomelevel": "Upper middle",
            "#meta+bool+deprecated": "N",
            "#meta+bool+independent": "Y",
            "#meta+id": "28",
            "#region+code+intermediate": "",
            "#region+code+main": "150",
            "#region+code+sub": "39",
            "#region+intermediate+name+preferred": "",
            "#region+main+name+preferred": "Europe",
            "#region+name+preferred+sub": "Southern Europe",
        }
        assert Country.get_country_info_from_iso3("PSE") == {
            "#country+alt+i_ar+name+v_unterm": "دولة فلسطين",
            "#country+alt+i_en+name+v_unterm": "State of Palestine",
            "#country+alt+i_es+name+v_unterm": "Estado de Palestina (el)",
            "#country+alt+i_fr+name+v_unterm": "État de Palestine (l')",
            "#country+alt+i_ru+name+v_unterm": "Государство Палестина",
            "#country+alt+i_zh+name+v_unterm": "巴勒斯坦国",
            "#country+alt+name+v_dgacm": "",
            "#country+alt+name+v_fts": "occupied Palestinian territory",
            "#country+alt+name+v_hrinfo_country": "occupied Palestinian territory",
            "#country+alt+name+v_iso": "Palestine, State of",
            "#country+alt+name+v_m49": "",
            "#country+alt+name+v_reliefweb": "occupied Palestinian territory",
            "#country+code+num+v_m49": "275",
            "#country+code+v_fts": "171",
            "#country+code+v_hrinfo_country": "351",
            "#country+code+v_iso2": "PS",
            "#country+code+v_iso3": "PSE",
            "#country+code+v_reliefweb": "180",
            "#country+formal+i_en+name+v_unterm": "the State of Palestine",
            "#country+name+override": "oPt",
            "#country+name+preferred": "State of Palestine",
            "#country+name+short+v_reliefweb": "oPt",
            "#country+regex": "palestin|\\bgaza|west.?bank",
            "#currency+code": "ILS",
            "#date+start": "2013-02-06",
            "#geo+admin_level": "0",
            "#geo+lat": "31.99084142",
            "#geo+lon": "35.30744047",
            "#indicator+incomelevel": "Upper middle",
            "#meta+bool+deprecated": "N",
            "#meta+bool+independent": "Y",
            "#meta+id": "170",
            "#region+code+intermediate": "",
            "#region+code+main": "142",
            "#region+code+sub": "145",
            "#region+intermediate+name+preferred": "",
            "#region+main+name+preferred": "Asia",
            "#region+name+preferred+sub": "Western Asia",
        }

    def test_get_currency_from_iso3(self):
        assert Country.get_currency_from_iso3("jpn") == "JPY"
        assert Country.get_currency_from_iso3("abc") is None
        with pytest.raises(LocationError):
            Country.get_currency_from_iso3("abc", exception=LocationError)

    def test_get_country_info_from_iso2(self):
        assert Country.get_country_info_from_iso2("jp") == {
            "#country+alt+i_ar+name+v_unterm": "اليابان",
            "#country+alt+i_en+name+v_unterm": "Japan",
            "#country+alt+i_es+name+v_unterm": "Japón (el)",
            "#country+alt+i_fr+name+v_unterm": "Japon (le)",
            "#country+alt+i_ru+name+v_unterm": "Япония",
            "#country+alt+i_zh+name+v_unterm": "日本",
            "#country+alt+name+v_dgacm": "",
            "#country+alt+name+v_fts": "",
            "#country+alt+name+v_hrinfo_country": "",
            "#country+alt+name+v_iso": "",
            "#country+alt+name+v_m49": "",
            "#country+alt+name+v_reliefweb": "",
            "#country+code+num+v_m49": "392",
            "#country+code+v_fts": "112",
            "#country+code+v_hrinfo_country": "292",
            "#country+code+v_iso2": "JP",
            "#country+code+v_iso3": "JPN",
            "#country+code+v_reliefweb": "128",
            "#country+formal+i_en+name+v_unterm": "Japan",
            "#country+name+preferred": "Japan",
            "#country+name+short+v_reliefweb": "",
            "#country+regex": "japan",
            "#currency+code": "JPY",
            "#date+start": "1974-01-01",
            "#geo+admin_level": "0",
            "#geo+lat": "37.63209801",
            "#geo+lon": "138.0812256",
            "#indicator+incomelevel": "High",
            "#meta+bool+deprecated": "N",
            "#meta+bool+independent": "Y",
            "#meta+id": "112",
            "#region+code+intermediate": "",
            "#region+code+main": "142",
            "#region+code+sub": "30",
            "#region+intermediate+name+preferred": "",
            "#region+main+name+preferred": "Asia",
            "#region+name+preferred+sub": "Eastern Asia",
        }
        assert Country.get_country_info_from_iso2("ab") is None
        assert Country.get_country_info_from_iso2("TW") == {
            "#country+alt+i_ar+name+v_unterm": "",
            "#country+alt+i_en+name+v_unterm": "Taiwan (Province of China)",
            "#country+alt+i_es+name+v_unterm": "",
            "#country+alt+i_fr+name+v_unterm": "",
            "#country+alt+i_ru+name+v_unterm": "",
            "#country+alt+i_zh+name+v_unterm": "",
            "#country+alt+name+v_dgacm": "",
            "#country+alt+name+v_fts": "Taiwan, Province of China",
            "#country+alt+name+v_hrinfo_country": "Taiwan, Province of China",
            "#country+alt+name+v_iso": "",
            "#country+alt+name+v_m49": "",
            "#country+alt+name+v_reliefweb": "China - Taiwan Province",
            "#country+code+num+v_m49": "158",
            "#country+code+v_fts": "219",
            "#country+code+v_hrinfo_country": "399",
            "#country+code+v_iso2": "TW",
            "#country+code+v_iso3": "TWN",
            "#country+code+v_reliefweb": "61",
            "#country+formal+i_en+name+v_unterm": "",
            "#country+name+preferred": "Taiwan (Province of China)",
            "#country+name+short+v_reliefweb": "",
            "#country+regex": ".*taiwan|.*taipei|.*formosa|^(?!.*\\bdem)(?!.*\\bpe)(?!.*\\bdr)(^rep.*).*\\bchina.*(?!.*\\bdem.*)(?!\\bpe.*)(?!.*\\bdr.*).*|^ROC$|^taiwan r\\.?o\\.?c\\.?$",
            "#currency+code": "TWD",
            "#date+start": "1974-01-01",
            "#geo+admin_level": "0",
            "#geo+lat": "23.74652012",
            "#geo+lon": "120.9621301",
            "#indicator+incomelevel": "High",
            "#meta+bool+deprecated": "N",
            "#meta+bool+independent": "N",
            "#meta+id": "218",
            "#region+code+intermediate": "",
            "#region+code+main": "142",
            "#region+code+sub": "30",
            "#region+intermediate+name+preferred": "",
            "#region+main+name+preferred": "Asia",
            "#region+name+preferred+sub": "Eastern Asia",
        }

        assert Country.get_country_info_from_iso2("PS") == {
            "#country+alt+i_ar+name+v_unterm": "دولة فلسطين",
            "#country+alt+i_en+name+v_unterm": "State of Palestine",
            "#country+alt+i_es+name+v_unterm": "Estado de Palestina (el)",
            "#country+alt+i_fr+name+v_unterm": "État de Palestine (l')",
            "#country+alt+i_ru+name+v_unterm": "Государство Палестина",
            "#country+alt+i_zh+name+v_unterm": "巴勒斯坦国",
            "#country+alt+name+v_dgacm": "",
            "#country+alt+name+v_fts": "occupied Palestinian territory",
            "#country+alt+name+v_hrinfo_country": "occupied Palestinian territory",
            "#country+alt+name+v_iso": "Palestine, State of",
            "#country+alt+name+v_m49": "",
            "#country+alt+name+v_reliefweb": "occupied Palestinian territory",
            "#country+code+num+v_m49": "275",
            "#country+code+v_fts": "171",
            "#country+code+v_hrinfo_country": "351",
            "#country+code+v_iso2": "PS",
            "#country+code+v_iso3": "PSE",
            "#country+code+v_reliefweb": "180",
            "#country+formal+i_en+name+v_unterm": "the State of Palestine",
            "#country+name+override": "oPt",
            "#country+name+preferred": "State of Palestine",
            "#country+name+short+v_reliefweb": "oPt",
            "#country+regex": "palestin|\\bgaza|west.?bank",
            "#currency+code": "ILS",
            "#date+start": "2013-02-06",
            "#geo+admin_level": "0",
            "#geo+lat": "31.99084142",
            "#geo+lon": "35.30744047",
            "#indicator+incomelevel": "Upper middle",
            "#meta+bool+deprecated": "N",
            "#meta+bool+independent": "Y",
            "#meta+id": "170",
            "#region+code+intermediate": "",
            "#region+code+main": "142",
            "#region+code+sub": "145",
            "#region+intermediate+name+preferred": "",
            "#region+main+name+preferred": "Asia",
            "#region+name+preferred+sub": "Western Asia",
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
        assert (
            Country.get_country_name_from_iso2("TW")
            == "Taiwan (Province of China)"
        )
        assert Country.get_country_name_from_iso2("PS") == "oPt"

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
            "#country+alt+i_ar+name+v_unterm": "أفغانستان",
            "#country+alt+i_en+name+v_unterm": "Afghanistan",
            "#country+alt+i_es+name+v_unterm": "Afganistán (el)",
            "#country+alt+i_fr+name+v_unterm": "Afghanistan (l')",
            "#country+alt+i_ru+name+v_unterm": "Афганистан",
            "#country+alt+i_zh+name+v_unterm": "阿富汗",
            "#country+alt+name+v_dgacm": "",
            "#country+alt+name+v_fts": "",
            "#country+alt+name+v_hrinfo_country": "",
            "#country+alt+name+v_iso": "",
            "#country+alt+name+v_m49": "",
            "#country+alt+name+v_reliefweb": "",
            "#country+code+num+v_m49": "4",
            "#country+code+v_fts": "1",
            "#country+code+v_hrinfo_country": "181",
            "#country+code+v_iso2": "AF",
            "#country+code+v_iso3": "AFG",
            "#country+code+v_reliefweb": "13",
            "#country+formal+i_en+name+v_unterm": "the Islamic Republic of Afghanistan",
            "#country+name+preferred": "Afghanistan",
            "#country+name+short+v_reliefweb": "",
            "#country+regex": "afghan",
            "#currency+code": "AFN",
            "#date+start": "2004-01-26",
            "#geo+admin_level": "0",
            "#geo+lat": "33.83147477",
            "#geo+lon": "66.02621828",
            "#indicator+incomelevel": "Low",
            "#meta+bool+deprecated": "N",
            "#meta+bool+independent": "Y",
            "#meta+id": "1",
            "#region+code+intermediate": "",
            "#region+code+main": "142",
            "#region+code+sub": "34",
            "#region+intermediate+name+preferred": "",
            "#region+main+name+preferred": "Asia",
            "#region+name+preferred+sub": "Southern Asia",
        }
        assert Country.get_country_info_from_m49(882) == {
            "#country+alt+i_ar+name+v_unterm": "ساموا",
            "#country+alt+i_en+name+v_unterm": "Samoa",
            "#country+alt+i_es+name+v_unterm": "Samoa",
            "#country+alt+i_fr+name+v_unterm": "Samoa (le)",
            "#country+alt+i_ru+name+v_unterm": "Самоа",
            "#country+alt+i_zh+name+v_unterm": "萨摩亚",
            "#country+alt+name+v_dgacm": "",
            "#country+alt+name+v_fts": "",
            "#country+alt+name+v_hrinfo_country": "",
            "#country+alt+name+v_iso": "",
            "#country+alt+name+v_m49": "",
            "#country+alt+name+v_reliefweb": "",
            "#country+code+num+v_m49": "882",
            "#country+code+v_fts": "193",
            "#country+code+v_hrinfo_country": "373",
            "#country+code+v_iso2": "WS",
            "#country+code+v_iso3": "WSM",
            "#country+code+v_reliefweb": "204",
            "#country+formal+i_en+name+v_unterm": "the Independent State of Samoa",
            "#country+name+preferred": "Samoa",
            "#country+name+short+v_reliefweb": "",
            "#country+regex": "^(?!.*amer.*)samoa|(\\bindep.*samoa)|^west.*samoa",
            "#currency+code": "WST",
            "#date+start": "1998-02-05",
            "#geo+admin_level": "0",
            "#geo+lat": "-13.16992041",
            "#geo+lon": "-173.5139768",
            "#indicator+incomelevel": "Lower middle",
            "#meta+bool+deprecated": "N",
            "#meta+bool+independent": "Y",
            "#meta+id": "192",
            "#region+code+intermediate": "",
            "#region+code+main": "9",
            "#region+code+sub": "61",
            "#region+intermediate+name+preferred": "",
            "#region+main+name+preferred": "Oceania",
            "#region+name+preferred+sub": "Polynesia",
        }
        assert Country.get_country_info_from_m49(275) == {
            "#country+alt+i_ar+name+v_unterm": "دولة فلسطين",
            "#country+alt+i_en+name+v_unterm": "State of Palestine",
            "#country+alt+i_es+name+v_unterm": "Estado de Palestina (el)",
            "#country+alt+i_fr+name+v_unterm": "État de Palestine (l')",
            "#country+alt+i_ru+name+v_unterm": "Государство Палестина",
            "#country+alt+i_zh+name+v_unterm": "巴勒斯坦国",
            "#country+alt+name+v_dgacm": "",
            "#country+alt+name+v_fts": "occupied Palestinian territory",
            "#country+alt+name+v_hrinfo_country": "occupied Palestinian territory",
            "#country+alt+name+v_iso": "Palestine, State of",
            "#country+alt+name+v_m49": "",
            "#country+alt+name+v_reliefweb": "occupied Palestinian territory",
            "#country+code+num+v_m49": "275",
            "#country+code+v_fts": "171",
            "#country+code+v_hrinfo_country": "351",
            "#country+code+v_iso2": "PS",
            "#country+code+v_iso3": "PSE",
            "#country+code+v_reliefweb": "180",
            "#country+formal+i_en+name+v_unterm": "the State of Palestine",
            "#country+name+override": "oPt",
            "#country+name+preferred": "State of Palestine",
            "#country+name+short+v_reliefweb": "oPt",
            "#country+regex": "palestin|\\bgaza|west.?bank",
            "#currency+code": "ILS",
            "#date+start": "2013-02-06",
            "#geo+admin_level": "0",
            "#geo+lat": "31.99084142",
            "#geo+lon": "35.30744047",
            "#indicator+incomelevel": "Upper middle",
            "#meta+bool+deprecated": "N",
            "#meta+bool+independent": "Y",
            "#meta+id": "170",
            "#region+code+intermediate": "",
            "#region+code+main": "142",
            "#region+code+sub": "145",
            "#region+intermediate+name+preferred": "",
            "#region+main+name+preferred": "Asia",
            "#region+name+preferred+sub": "Western Asia",
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
        assert Country.expand_countryname_abbrevs(
            "Haha Dem. Fed. Republic"
        ) == [
            "HAHA DEMOCRATIC FED. REPUBLIC",
            "HAHA DEMOCRATIC FEDERATION REPUBLIC",
            "HAHA DEMOCRATIC FEDERAL REPUBLIC",
            "HAHA DEMOCRATIC FEDERATED REPUBLIC",
        ]

    def test_simplify_countryname(self):
        assert Country.simplify_countryname("jpn") == ("JPN", list())
        assert Country.simplify_countryname("United Rep. of Tanzania") == (
            "TANZANIA",
            ["UNITED", "REP", "OF"],
        )
        assert Country.simplify_countryname(
            "Micronesia (Federated States of)"
        ) == (
            "MICRONESIA",
            ["FEDERATED", "STATES", "OF"],
        )
        assert Country.simplify_countryname("Dem. Rep. of the Congo") == (
            "CONGO",
            ["DEM", "REP", "OF", "THE"],
        )
        assert Country.simplify_countryname(
            "Korea, Democratic People's Republic of"
        ) == ("KOREA", ["DEMOCRATIC", "PEOPLE'S", "REPUBLIC", "OF"])
        assert Country.simplify_countryname(
            "Democratic People's Republic of Korea"
        ) == ("KOREA", ["DEMOCRATIC", "PEOPLE'S", "REPUBLIC", "OF"])
        assert Country.simplify_countryname(
            "The former Yugoslav Republic of Macedonia"
        ) == ("MACEDONIA", ["THE", "FORMER", "YUGOSLAV", "REPUBLIC", "OF"])

    def test_get_iso3_country_code(self):
        assert Country.get_iso3_country_code("jpn") == "JPN"
        assert Country.get_iso3_country_code("Dem. Rep. of the Congo") == "COD"
        assert Country.get_iso3_country_code("Russian Fed.") == "RUS"
        assert Country.get_iso3_country_code("中国") == "CHN"
        assert (
            Country.get_iso3_country_code("المملكة العربية السعودية") == "SAU"
        )
        assert (
            Country.get_iso3_country_code("Micronesia (Federated States of)")
            == "FSM"
        )
        assert Country.get_iso3_country_code("Iran (Islamic Rep. of)") == "IRN"
        assert (
            Country.get_iso3_country_code("United Rep. of Tanzania") == "TZA"
        )
        assert Country.get_iso3_country_code("Syrian Arab Rep.") == "SYR"
        assert Country.get_iso3_country_code("Central African Rep.") == "CAF"
        assert Country.get_iso3_country_code("Rep. of Korea") == "KOR"
        assert (
            Country.get_iso3_country_code("St. Pierre and Miquelon") == "SPM"
        )
        assert Country.get_iso3_country_code("Christmas Isl.") == "CXR"
        assert Country.get_iso3_country_code("Cayman Isl.") == "CYM"
        assert Country.get_iso3_country_code("jp") == "JPN"
        assert (
            Country.get_iso3_country_code("Taiwan (Province of China)")
            == "TWN"
        )
        assert Country.get_iso3_country_code("Congo DR") == "COD"
        assert Country.get_iso3_country_code("oPt") == "PSE"
        assert (
            Country.get_iso3_country_code("Lao People's Democratic Republic")
            == "LAO"
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
            Country.get_iso3_country_code_fuzzy(
                "abcde", exception=LocationError
            )
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
        assert Country.get_iso3_country_code_fuzzy(
            "united states of america"
        ) == (
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
        assert Country.get_iso3_country_code_fuzzy(
            "Congo, Democratic Republic"
        ) == (
            "COD",
            False,
        )
        assert Country.get_iso3_country_code_fuzzy("Congo, Republic of") == (
            "COG",
            False,
        )
        assert Country.get_iso3_country_code_fuzzy(
            "Republic of the Congo"
        ) == (
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
            Country.get_countries_in_region(
                "NOTEXIST", exception=LocationError
            )

    def test_ocha_feed_file_working(self):
        countries = hxl.data(
            script_dir_plus_file("Countries_UZB_Deleted.csv", TestCountry),
            InputOptions(allow_local=True, encoding="utf-8"),
        )
        Country.set_countriesdata(countries)
        assert Country.get_iso3_country_code("UZBEKISTAN") is None
        assert Country.get_iso3_country_code("south sudan") == "SSD"
        Country.set_ocha_url()
        Country._countriesdata = None
        assert (
            Country.get_iso3_country_code("UZBEKISTAN", use_live=True) == "UZB"
        )
        assert Country.get_iso3_country_code_fuzzy("Laos") == ("LAO", False)
        Country.set_ocha_url("NOTEXIST")
        Country._countriesdata = None
        assert Country.get_iso3_from_iso2("AF") == "AFG"
