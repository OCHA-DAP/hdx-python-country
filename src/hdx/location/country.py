"""Country location"""

import copy
import logging
import re
from string import punctuation
from typing import Dict, List, Optional, Tuple, Union

import hxl
from hxl import InputOptions

from hdx.utilities.path import script_dir_plus_file
from hdx.utilities.text import get_words_in_sentence
from hdx.utilities.typehint import ExceptionUpperBound

logger = logging.getLogger(__name__)


class CountryError(Exception):
    pass


class Country:
    """Country class with various methods to help with mapping between country and
    region names and codes. Uses OCHA's countries and territories feed.
    """

    abbreviations = {
        "DEM.": "DEMOCRATIC",
        "FMR.": "FORMER",
        "PROV.": "PROVINCE",
        "REP.": "REPUBLIC",
        "ST.": "SAINT",
        "UTD.": "UNITED",
        "U.": "UNITED",
        "N.": "NORTH",
        "E.": "EAST",
        "W.": "WEST",
        "K.": "KINGDOM",
    }
    major_differentiators = [
        "DEMOCRATIC",
        "NORTH",
        "SOUTH",
        "EAST",
        "WEST",
        "STATES",
    ]
    multiple_abbreviations = {
        "FED.": ["FEDERATION", "FEDERAL", "FEDERATED"],
        "ISL.": ["ISLAND", "ISLANDS"],
        "S.": ["SOUTH", "STATES"],
        "TERR.": ["TERRITORY", "TERRITORIES"],
    }
    simplifications = [
        "AND",
        "THE",
        "OF",
        "ISLAMIC",
        "STATES",
        "BOLIVARIAN",
        "PLURINATIONAL",
        "PEOPLE'S",
        "DUTCH PART",
        "FRENCH PART",
        "MALVINAS",
        "YUGOSLAV",
        "KINGDOM",
        "PROTECTORATE",
    ]
    _countriesdata = None
    _ochaurl_default = "https://docs.google.com/spreadsheets/d/1NjSI2LaS3SqbgYc0HdD8oIb7lofGtiHgoKKATCpwVdY/export?format=csv&gid=1088874596"
    _ochaurl = _ochaurl_default
    _country_name_overrides = {}
    _country_name_mappings = {}

    @classmethod
    def _add_countriesdata(cls, iso3: str, hxlcountry: hxl.Row) -> Dict:
        """
        Set up countries data from data in form provided by UNStats and World Bank

        Args:
            iso3 (str): ISO3 code for country
            hxlcountry (hxl.Row): Country information

        Returns:
            Dict: Country dictionary
        """
        country = hxlcountry.dictionary
        for value in hxlcountry.get_all("#country+name"):
            if value:
                cls._countriesdata["countrynames2iso3"][value.upper()] = iso3
        countryname = cls._country_name_overrides.get(iso3)
        if countryname is not None:
            country["#country+name+override"] = countryname
        iso2 = hxlcountry.get("#country+code+v_iso2")
        if iso2:
            cls._countriesdata["iso2iso3"][iso2] = iso3
            # different types so keys won't clash
            cls._countriesdata["iso2iso3"][iso3] = iso2
        m49 = hxlcountry.get("#country+code+num+v_m49")
        if m49:
            m49 = int(m49)
            cls._countriesdata["m49iso3"][m49] = iso3
            # different types so keys won't clash
            cls._countriesdata["m49iso3"][iso3] = m49
        cls._countriesdata["aliases"][iso3] = re.compile(
            hxlcountry.get("#country+regex"), re.IGNORECASE
        )
        regionname = hxlcountry.get("#region+main+name+preferred")
        sub_regionname = hxlcountry.get("#region+name+preferred+sub")
        intermediate_regionname = hxlcountry.get(
            "#region+intermediate+name+preferred"
        )
        regionid = hxlcountry.get("#region+code+main")
        if regionid:
            regionid = int(regionid)
        sub_regionid = hxlcountry.get("#region+code+sub")
        if sub_regionid:
            sub_regionid = int(sub_regionid)
        intermediate_regionid = hxlcountry.get("#region+code+intermediate")
        if intermediate_regionid:
            intermediate_regionid = int(intermediate_regionid)

        # region, subregion and intermediate region codes do not clash so only need one dict
        def add_country_to_set(colname, idval, iso3):
            value = cls._countriesdata[colname].get(idval)
            if value is None:
                value = set()
                cls._countriesdata["regioncodes2countries"][idval] = value
            value.add(iso3)

        if regionname:
            add_country_to_set("regioncodes2countries", regionid, iso3)
            cls._countriesdata["regioncodes2names"][regionid] = regionname
            cls._countriesdata["regionnames2codes"][regionname.upper()] = (
                regionid
            )
        if sub_regionname:
            add_country_to_set("regioncodes2countries", sub_regionid, iso3)
            cls._countriesdata["regioncodes2names"][sub_regionid] = (
                sub_regionname
            )
            cls._countriesdata["regionnames2codes"][sub_regionname.upper()] = (
                sub_regionid
            )
        if intermediate_regionname:
            add_country_to_set(
                "regioncodes2countries", intermediate_regionid, iso3
            )
            cls._countriesdata["regioncodes2names"][intermediate_regionid] = (
                intermediate_regionname
            )
            cls._countriesdata["regionnames2codes"][
                intermediate_regionname.upper()
            ] = intermediate_regionid
        currency = hxlcountry.get("#currency+code")
        cls._countriesdata["currencies"][iso3] = currency
        return country

    @classmethod
    def set_countriesdata(cls, countries: str) -> None:
        """
        Set up countries data from data in form provided by UNStats and World Bank

        Args:
            countries (str): Countries data in HTML format provided by UNStats

        Returns:
            None
        """
        cls._countriesdata = {}
        cls._countriesdata["countries"] = {}
        cls._countriesdata["iso2iso3"] = {}
        cls._countriesdata["m49iso3"] = {}
        cls._countriesdata["countrynames2iso3"] = {}
        cls._countriesdata["regioncodes2countries"] = {}
        cls._countriesdata["regioncodes2names"] = {}
        cls._countriesdata["regionnames2codes"] = {}
        cls._countriesdata["aliases"] = {}
        cls._countriesdata["currencies"] = {}

        for key, value in cls._country_name_mappings.items():
            cls._countriesdata["countrynames2iso3"][key.upper()] = (
                value.upper()
            )

        for country in countries:
            iso3 = country.get("#country+code+v_iso3")
            if not iso3:
                continue
            iso3 = iso3.upper()
            countrydict = cls._add_countriesdata(iso3, country)
            cls._countriesdata["countries"][iso3] = countrydict

        def sort_list(colname):
            for idval in cls._countriesdata[colname]:
                cls._countriesdata[colname][idval] = sorted(
                    list(cls._countriesdata[colname][idval])
                )

        sort_list("regioncodes2countries")

    @classmethod
    def countriesdata(
        cls,
        use_live: bool = True,
        country_name_overrides: Dict = None,
        country_name_mappings: Dict = None,
    ) -> List[Dict[str, Dict]]:
        """
        Read countries data from OCHA countries feed (falling back to file)

        Args:
            use_live (bool): Try to get use latest data from web rather than file in package. Defaults to True.
            country_name_overrides (Dict): Dictionary of mappings from iso3 to country name
            country_name_mappings (Dict): Dictionary of mappings from country name to iso3

        Returns:
            List[Dict[str,Dict]]: Countries dictionaries
        """
        if cls._countriesdata is None:
            countries = None
            if country_name_overrides is not None:
                cls.set_country_name_overrides(country_name_overrides)
            if country_name_mappings is not None:
                cls.set_country_name_mappings(country_name_mappings)
            if use_live:
                try:
                    countries = hxl.data(
                        cls._ochaurl, InputOptions(encoding="utf-8")
                    )
                except OSError:
                    logger.exception(
                        "Download from OCHA feed failed! Falling back to stored file."
                    )
            if countries is None:
                countries = hxl.data(
                    script_dir_plus_file(
                        "Countries & Territories Taxonomy MVP - C&T Taxonomy with HXL Tags.csv",
                        Country,
                    ),
                    InputOptions(allow_local=True, encoding="utf-8"),
                )
            cls.set_countriesdata(countries)
        return cls._countriesdata

    @classmethod
    def set_ocha_url(cls, url: Optional[str] = None) -> None:
        """
        Set OCHA url from which to retrieve countries data

        Args:
            url (Optional[str]): OCHA url from which to retrieve countries data. Defaults to internal value.

        Returns:
            None
        """
        if url is None:
            url = cls._ochaurl_default
        cls._ochaurl = url

    @classmethod
    def set_country_name_overrides(cls, country_name_overrides: Dict) -> None:
        """
        Setup name overrides using dictionary of mappings from iso3 to country name

        Args:
            country_name_overrides (Dict): Dictionary of mappings from iso3 to country name

        Returns:
            None
        """
        cls._country_name_overrides = country_name_overrides

    @classmethod
    def set_country_name_mappings(cls, country_name_mappings: Dict) -> None:
        """
        Setup additional name mappings using dictionary of mappings from country name to iso3

        Args:
            country_name_mappings (Dict): Dictionary of mappings from country name to iso3

        Returns:
            None
        """
        cls._country_name_mappings = country_name_mappings

    @classmethod
    def get_country_info_from_iso3(
        cls,
        iso3: str,
        use_live: bool = True,
        exception: Optional[ExceptionUpperBound] = None,
    ) -> Optional[Dict[str, str]]:
        """Get country information from ISO3 code

        Args:
            iso3 (str): ISO3 code for which to get country information
            use_live (bool): Try to get use latest data from web rather than file in package. Defaults to True.
            exception (Optional[ExceptionUpperBound]): An exception to raise if country not found. Defaults to None.

        Returns:
            Optional[Dict[str,str]]: country information
        """
        countriesdata = cls.countriesdata(use_live=use_live)
        country = countriesdata["countries"].get(iso3.upper())
        if country is not None:
            return country

        if exception is not None:
            raise exception
        return None

    @classmethod
    def get_country_name_from_iso3(
        cls,
        iso3: str,
        use_live: bool = True,
        exception: Optional[ExceptionUpperBound] = None,
        formal: bool = False,
    ) -> Optional[str]:
        """Get country name from ISO3 code

        Args:
            iso3 (str): ISO3 code for which to get country name
            use_live (bool): Try to get use latest data from web rather than file in package. Defaults to True.
            exception (Optional[ExceptionUpperBound]): An exception to raise if country not found. Defaults to None.
            formal (bool): Return preferred name if False, formal name if True. Defaults to False.

        Returns:
            Optional[str]: Country name
        """
        countryinfo = cls.get_country_info_from_iso3(
            iso3, use_live=use_live, exception=exception
        )
        if countryinfo is not None:
            countryname = countryinfo.get("#country+name+override")
            if countryname is not None:
                return countryname
            if formal:
                countryname = countryinfo.get(
                    "#country+formal+i_en+name+v_unterm"
                )
                if countryname is None or countryname == "":
                    countryname = countryinfo.get("#country+name+preferred")
                return countryname
            else:
                return countryinfo.get("#country+name+preferred")
        return None

    @classmethod
    def get_currency_from_iso3(
        cls,
        iso3: str,
        use_live: bool = True,
        exception: Optional[ExceptionUpperBound] = None,
    ) -> Optional[int]:
        """Get currency code from ISO3 code

        Args:
            iso3 (str): ISO3 code for which to get M49 code
            use_live (bool): Try to get use latest data from web rather than file in package. Defaults to True.
            exception (Optional[ExceptionUpperBound]): An exception to raise if country not found. Defaults to None.

        Returns:
            Optional[str]: Currency code
        """
        countriesdata = cls.countriesdata(use_live=use_live)
        currency = countriesdata["currencies"].get(iso3.upper())
        if currency is not None:
            return currency

        if exception is not None:
            raise exception
        return None

    @classmethod
    def get_iso2_from_iso3(
        cls,
        iso3: str,
        use_live: bool = True,
        exception: Optional[ExceptionUpperBound] = None,
    ) -> Optional[str]:
        """Get ISO2 from ISO3 code

        Args:
            iso3 (str): ISO3 code for which to get ISO2 code
            use_live (bool): Try to get use latest data from web rather than file in package. Defaults to True.
            exception (Optional[ExceptionUpperBound]): An exception to raise if country not found. Defaults to None.

        Returns:
            Optional[str]: ISO2 code
        """
        countriesdata = cls.countriesdata(use_live=use_live)
        iso2 = countriesdata["iso2iso3"].get(iso3.upper())
        if iso2 is not None:
            return iso2

        if exception is not None:
            raise exception
        return None

    @classmethod
    def get_iso3_from_iso2(
        cls,
        iso2: str,
        use_live: bool = True,
        exception: Optional[ExceptionUpperBound] = None,
    ) -> Optional[str]:
        """Get ISO3 from ISO2 code

        Args:
            iso2 (str): ISO2 code for which to get ISO3 code
            use_live (bool): Try to get use latest data from web rather than file in package. Defaults to True.
            exception (Optional[ExceptionUpperBound]): An exception to raise if country not found. Defaults to None.

        Returns:
            Optional[str]: ISO3 code
        """
        countriesdata = cls.countriesdata(use_live=use_live)
        iso3 = countriesdata["iso2iso3"].get(iso2.upper())
        if iso3 is not None:
            return iso3

        if exception is not None:
            raise exception
        return None

    @classmethod
    def get_country_info_from_iso2(
        cls,
        iso2: str,
        use_live: bool = True,
        exception: Optional[ExceptionUpperBound] = None,
    ) -> Optional[Dict[str, str]]:
        """Get country name from ISO2 code

        Args:
            iso2 (str): ISO2 code for which to get country information
            use_live (bool): Try to get use latest data from web rather than file in package. Defaults to True.
            exception (Optional[ExceptionUpperBound]): An exception to raise if country not found. Defaults to None.

        Returns:
            Optional[Dict[str,str]]: Country information
        """
        iso3 = cls.get_iso3_from_iso2(
            iso2, use_live=use_live, exception=exception
        )
        if iso3 is not None:
            return cls.get_country_info_from_iso3(
                iso3, use_live=use_live, exception=exception
            )
        return None

    @classmethod
    def get_country_name_from_iso2(
        cls,
        iso2: str,
        use_live: bool = True,
        exception: Optional[ExceptionUpperBound] = None,
        formal: bool = False,
    ) -> Optional[str]:
        """Get country name from ISO2 code

        Args:
            iso2 (str): ISO2 code for which to get country name
            use_live (bool): Try to get use latest data from web rather than file in package. Defaults to True.
            exception (Optional[ExceptionUpperBound]): An exception to raise if country not found. Defaults to None.
            formal (bool): Return preferred name if False, formal name if True. Defaults to False.

        Returns:
            Optional[str]: Country name
        """
        iso3 = cls.get_iso3_from_iso2(
            iso2, use_live=use_live, exception=exception
        )
        if iso3 is not None:
            return cls.get_country_name_from_iso3(
                iso3, exception=exception, formal=formal
            )
        return None

    @classmethod
    def get_currency_from_iso2(
        cls,
        iso2: str,
        use_live: bool = True,
        exception: Optional[ExceptionUpperBound] = None,
    ) -> Optional[str]:
        """Get currency from ISO2 code

        Args:
            iso2 (str): ISO2 code for which to get country information
            use_live (bool): Try to get use latest data from web rather than file in package. Defaults to True.
            exception (Optional[ExceptionUpperBound]): An exception to raise if country not found. Defaults to None.

        Returns:
            Optional[str]: Currency
        """
        iso3 = cls.get_iso3_from_iso2(
            iso2, use_live=use_live, exception=exception
        )
        if iso3 is not None:
            return cls.get_currency_from_iso3(
                iso3, use_live=use_live, exception=exception
            )
        return None

    @classmethod
    def get_m49_from_iso3(
        cls,
        iso3: str,
        use_live: bool = True,
        exception: Optional[ExceptionUpperBound] = None,
    ) -> Optional[int]:
        """Get M49 from ISO3 code

        Args:
            iso3 (str): ISO3 code for which to get M49 code
            use_live (bool): Try to get use latest data from web rather than file in package. Defaults to True.
            exception (Optional[ExceptionUpperBound]): An exception to raise if country not found. Defaults to None.

        Returns:
            Optional[int]: M49 code
        """
        countriesdata = cls.countriesdata(use_live=use_live)
        m49 = countriesdata["m49iso3"].get(iso3)
        if m49 is not None:
            return m49

        if exception is not None:
            raise exception
        return None

    @classmethod
    def get_iso3_from_m49(
        cls,
        m49: int,
        use_live: bool = True,
        exception: Optional[ExceptionUpperBound] = None,
    ) -> Optional[str]:
        """Get ISO3 from M49 code

        Args:
            m49 (int): M49 numeric code for which to get ISO3 code
            use_live (bool): Try to get use latest data from web rather than file in package. Defaults to True.
            exception (Optional[ExceptionUpperBound]): An exception to raise if country not found. Defaults to None.

        Returns:
            Optional[str]: ISO3 code
        """
        countriesdata = cls.countriesdata(use_live=use_live)
        iso3 = countriesdata["m49iso3"].get(m49)
        if iso3 is not None:
            return iso3

        if exception is not None:
            raise exception
        return None

    @classmethod
    def get_country_info_from_m49(
        cls,
        m49: int,
        use_live: bool = True,
        exception: Optional[ExceptionUpperBound] = None,
    ) -> Optional[Dict[str, str]]:
        """Get country name from M49 code

        Args:
            m49 (int): M49 numeric code for which to get country information
            use_live (bool): Try to get use latest data from web rather than file in package. Defaults to True.
            exception (Optional[ExceptionUpperBound]): An exception to raise if country not found. Defaults to None.

        Returns:
            Optional[Dict[str,str]]: Country information
        """
        iso3 = cls.get_iso3_from_m49(
            m49, use_live=use_live, exception=exception
        )
        if iso3 is not None:
            return cls.get_country_info_from_iso3(iso3, exception=exception)
        return None

    @classmethod
    def get_country_name_from_m49(
        cls,
        m49: int,
        use_live: bool = True,
        exception: Optional[ExceptionUpperBound] = None,
        formal: bool = False,
    ) -> Optional[str]:
        """Get country name from M49 code

        Args:
            m49 (int): M49 numeric code for which to get country name
            use_live (bool): Try to get use latest data from web rather than file in package. Defaults to True.
            exception (Optional[ExceptionUpperBound]): An exception to raise if country not found. Defaults to None.
            formal (bool): Return preferred name if False, formal name if True. Defaults to False.

        Returns:
            Optional[str]: Country name
        """
        iso3 = cls.get_iso3_from_m49(
            m49, use_live=use_live, exception=exception
        )
        if iso3 is not None:
            return cls.get_country_name_from_iso3(
                iso3, exception=exception, formal=formal
            )
        return None

    @classmethod
    def get_currency_from_m49(
        cls,
        m49: int,
        use_live: bool = True,
        exception: Optional[ExceptionUpperBound] = None,
    ) -> Optional[str]:
        """Get currency from M49 code

        Args:
            m49 (int): M49 numeric code for which to get country name
            use_live (bool): Try to get use latest data from web rather than file in package. Defaults to True.
            exception (Optional[ExceptionUpperBound]): An exception to raise if country not found. Defaults to None.

        Returns:
            Optional[str]: Currency
        """
        iso3 = cls.get_iso3_from_m49(
            m49, use_live=use_live, exception=exception
        )
        if iso3 is not None:
            return cls.get_currency_from_iso3(
                iso3, use_live=use_live, exception=exception
            )
        return None

    @classmethod
    def expand_countryname_abbrevs(cls, country: str) -> List[str]:
        """Expands abbreviation(s) in country name in various ways (eg. FED -> FEDERATED, FEDERAL etc.)

        Args:
            country (str): Country with abbreviation(s)to expand

        Returns:
            List[str]: Uppercase country name with abbreviation(s) expanded in various ways
        """

        def replace_ensure_space(word, replace, replacement):
            return (
                word.replace(replace, f"{replacement} ")
                .replace("  ", " ")
                .strip()
            )

        countryupper = country.upper()
        for abbreviation in cls.abbreviations:
            countryupper = replace_ensure_space(
                countryupper, abbreviation, cls.abbreviations[abbreviation]
            )
        candidates = [countryupper]
        for abbreviation in cls.multiple_abbreviations:
            if abbreviation in countryupper:
                for expanded in cls.multiple_abbreviations[abbreviation]:
                    candidates.append(
                        replace_ensure_space(
                            countryupper, abbreviation, expanded
                        )
                    )
        return candidates

    @classmethod
    def simplify_countryname(cls, country: str) -> (str, List[str]):
        """Simplifies country name by removing descriptive text eg. DEMOCRATIC, REPUBLIC OF etc.

        Args:
            country (str): Country name to simplify

        Returns:
            Tuple[str, List[str]]: Uppercase simplified country name and list of removed words
        """
        countryupper = country.upper()
        words = get_words_in_sentence(countryupper)
        index = countryupper.find(",")
        if index != -1:
            countryupper = countryupper[:index]
        index = countryupper.find(":")
        if index != -1:
            countryupper = countryupper[:index]
        regex = re.compile(r"\(.+?\)")
        countryupper = regex.sub("", countryupper)
        remove = copy.deepcopy(cls.simplifications)
        for simplification1, simplification2 in cls.abbreviations.items():
            countryupper = countryupper.replace(simplification1, "")
            remove.append(simplification2)
        for (
            simplification1,
            simplifications,
        ) in cls.multiple_abbreviations.items():
            countryupper = countryupper.replace(simplification1, "")
            for simplification2 in simplifications:
                remove.append(simplification2)
        remove = "|".join(remove)
        regex = re.compile(r"\b(" + remove + r")\b", flags=re.IGNORECASE)
        countryupper = regex.sub("", countryupper)
        countryupper = countryupper.strip()
        countryupper_words = get_words_in_sentence(countryupper)
        if len(countryupper_words) > 1:
            countryupper = countryupper_words[0]
        if countryupper:
            countryupper = countryupper.strip(punctuation)
            words.remove(countryupper)
        return countryupper, words

    @classmethod
    def get_iso3_country_code(
        cls,
        country: str,
        use_live: bool = True,
        exception: Optional[ExceptionUpperBound] = None,
    ) -> Optional[str]:
        """Get ISO3 code for cls. Only exact matches or None are returned.

        Args:
            country (str): Country for which to get ISO3 code
            use_live (bool): Try to get use latest data from web rather than file in package. Defaults to True.
            exception (Optional[ExceptionUpperBound]): An exception to raise if country not found. Defaults to None.

        Returns:
            Optional[str]: ISO3 country code or None
        """
        countriesdata = cls.countriesdata(use_live=use_live)
        countryupper = country.strip().upper()
        if countryupper.isupper():
            len_countryupper = len(countryupper)
            if len_countryupper == 3:
                if countryupper in countriesdata["countries"]:
                    return countryupper
            elif len_countryupper == 2:
                iso3 = countriesdata["iso2iso3"].get(countryupper)
                if iso3 is not None:
                    return iso3

            iso3 = countriesdata["countrynames2iso3"].get(countryupper)
            if iso3 is not None:
                return iso3

            for candidate in cls.expand_countryname_abbrevs(countryupper):
                iso3 = countriesdata["countrynames2iso3"].get(candidate)
                if iso3 is not None:
                    return iso3
        elif re.search(r"[\u4e00-\u9fff]+", countryupper):
            for country in countriesdata["countries"]:
                if (
                    countriesdata["countries"][country][
                        "#country+alt+i_zh+name+v_unterm"
                    ]
                    == countryupper
                ):
                    return country
        elif re.search(r"[\u0600-\u06FF]+", countryupper):
            for country in countriesdata["countries"]:
                if (
                    countriesdata["countries"][country][
                        "#country+alt+i_ar+name+v_unterm"
                    ]
                    == countryupper
                ):
                    return country

        if exception is not None:
            raise exception
        return None

    @classmethod
    def get_iso3_country_code_fuzzy(
        cls,
        country: str,
        use_live: bool = True,
        exception: Optional[ExceptionUpperBound] = None,
        min_chars: int = 5,
    ) -> Tuple[Optional[str], bool]:
        """Get ISO3 code for cls. A tuple is returned with the first value being the ISO3 code and the second
        showing if the match is exact or not.

        Args:
            country (str): Country for which to get ISO3 code
            use_live (bool): Try to get use latest data from web rather than file in package. Defaults to True.
            exception (Optional[ExceptionUpperBound]): An exception to raise if country not found. Defaults to None.
            min_chars (int): Minimum number of characters for fuzzy matching to be tried. Defaults to 5.

        Returns:
            Tuple[Optional[str], bool]]: ISO3 code and if the match is exact or (None, False).
        """
        countriesdata = cls.countriesdata(use_live=use_live)
        country = country.strip()
        if not country.upper().isupper():
            return None, False

        iso3 = cls.get_iso3_country_code(country, use_live=use_live)
        # don't put exception param here as we don't want it to throw

        if iso3 is not None:
            return iso3, True

        # regex lookup
        for iso3, regex in countriesdata["aliases"].items():
            index = re.search(regex, country.upper())
            if index is not None:
                return iso3, False

        if len(country) < min_chars:
            return None, False

        def remove_matching_from_list(wordlist, word_or_part):
            for word in wordlist:
                if word_or_part in word:
                    wordlist.remove(word)
                    if word_or_part == word:
                        return 35
                    return 17

        # fuzzy matching
        expanded_country_candidates = cls.expand_countryname_abbrevs(country)
        match_strength = 0
        matches = set()
        for countryname in sorted(countriesdata["countrynames2iso3"]):
            for candidate in expanded_country_candidates:
                simplified_country, removed_words = cls.simplify_countryname(
                    candidate
                )
                if simplified_country in countryname:
                    words = get_words_in_sentence(countryname)
                    new_match_strength = remove_matching_from_list(
                        words, simplified_country
                    )
                    for word in removed_words:
                        if word in countryname:
                            remove_matching_from_list(words, word)
                            new_match_strength += 4
                        else:
                            if word in cls.major_differentiators:
                                new_match_strength -= 16
                            else:
                                new_match_strength -= 1
                    for word in words:
                        if word in cls.major_differentiators:
                            new_match_strength -= 16
                        else:
                            new_match_strength -= 1
                    iso3 = countriesdata["countrynames2iso3"][countryname]
                    if new_match_strength > match_strength:
                        match_strength = new_match_strength
                        matches = set()
                    if new_match_strength == match_strength:
                        matches.add(iso3)

        if len(matches) == 1 and match_strength > 16:
            return matches.pop(), False

        if exception is not None:
            raise exception
        return None, False

    @classmethod
    def get_countries_in_region(
        cls,
        region: Union[int, str],
        use_live: bool = True,
        exception: Optional[ExceptionUpperBound] = None,
    ) -> List[str]:
        """Get countries (ISO3 codes) in region

        Args:
            region (Union[int,str]): Three digit UNStats M49 region code or region name
            use_live (bool): Try to get use latest data from web rather than file in package. Defaults to True.
            exception (Optional[ExceptionUpperBound]): An exception to raise if region not found. Defaults to None.

        Returns:
            List(str): Sorted list of ISO3 country names
        """
        countriesdata = cls.countriesdata(use_live=use_live)
        if isinstance(region, int):
            regioncode = region
        else:
            regionupper = region.upper()
            regioncode = countriesdata["regionnames2codes"].get(regionupper)

        if regioncode is not None:
            return countriesdata["regioncodes2countries"][regioncode]

        if exception is not None:
            raise exception
        return []
