"""Country location"""

import logging
import os.path
import re
from collections.abc import Iterator
from pathlib import Path

from hdx.utilities.base_downloader import BaseDownload, DownloadError
from hdx.utilities.downloader import Download
from hdx.utilities.path import script_dir_plus_file
from hdx.utilities.text import get_words_in_sentence

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
        "PEOPLES",
        "DUTCH PART",
        "FRENCH PART",
        "MALVINAS",
        "YUGOSLAV",
        "KINGDOM",
        "PROTECTORATE",
    ]
    _include_unofficial_default = False
    _include_unofficial = _include_unofficial_default
    _use_live_default = True
    _use_live = _use_live_default
    _countriesdata = None
    _ochaurl_default = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSIIswgPn6oc_Ui3hCl2RTAdVZEw2sx4GjgqWFywrr8dt9R9B-p6Cs3jKeJigDguIbOjMxYtnloLlmI/pub?gid=1528390745&single=true&output=csv"
    _ochaurl = _ochaurl_default
    _ochapath_default = script_dir_plus_file(
        "Countries & Territories Taxonomy MVP - C&T Taxonomy.csv",
        CountryError,
    )
    _ochapath = _ochapath_default
    _country_name_overrides = {}
    _country_name_mappings = {}
    _country_name_keys = (
        "Preferred Term",
        "ISO Alt Term",
        "DGACM Alt Term",
        "HPC Tools Alt Term",
        "RW Short Name",
        "RW API Alt Term",
        "English Short",
        "French Short",
        "Spanish Short",
        "Russian Short",
        "Chinese Short",
        "Arabic Short",
        "English Formal",
        "M49 English",
        "M49 French",
        "M49 Spanish",
        "M49 Russian",
        "M49 Chinese",
        "M49 Arabic",
    )

    @classmethod
    def _add_countriesdata(cls, iso3: str, country: dict) -> dict:
        """
        Set up countries data from data in form provided by UNStats and World Bank

        Args:
            iso3: ISO3 code for country
            country: Country information

        Returns:
            Country dictionary
        """
        for key in cls._country_name_keys:
            value = country[key]
            if value:
                cls._countriesdata["countrynames2iso3"][value.upper()] = iso3
        countryname = cls._country_name_overrides.get(iso3)
        if countryname is not None:
            country["Name Override"] = countryname
        iso2 = country.get("ISO 3166-1 Alpha 2-Codes")
        if not iso2 and cls._include_unofficial:
            iso2 = country.get("x Alpha2 codes")
        if iso2:
            cls._countriesdata["iso2iso3"][iso2] = iso3
            # different types so keys won't clash
            cls._countriesdata["iso2iso3"][iso3] = iso2
        m49 = country.get("m49 numerical code")
        if m49:
            m49 = int(m49)
            cls._countriesdata["m49iso3"][m49] = iso3
            # different types so keys won't clash
            cls._countriesdata["m49iso3"][iso3] = m49
        cls._countriesdata["aliases"][iso3] = re.compile(
            country.get("Regex"), re.IGNORECASE
        )
        regionname = country.get("Region Name")
        sub_regionname = country.get("Sub-region Name")
        intermediate_regionname = country.get("Intermediate Region Name")
        regionid = country.get("Region Code")
        if regionid:
            regionid = int(regionid)
        sub_regionid = country.get("Sub-region Code")
        if sub_regionid:
            sub_regionid = int(sub_regionid)
        intermediate_regionid = country.get("Intermediate Region Code")
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
            cls._countriesdata["regionnames2codes"][regionname.upper()] = regionid
        if sub_regionname:
            add_country_to_set("regioncodes2countries", sub_regionid, iso3)
            cls._countriesdata["regioncodes2names"][sub_regionid] = sub_regionname
            cls._countriesdata["regionnames2codes"][sub_regionname.upper()] = (
                sub_regionid
            )
        if intermediate_regionname:
            add_country_to_set("regioncodes2countries", intermediate_regionid, iso3)
            cls._countriesdata["regioncodes2names"][intermediate_regionid] = (
                intermediate_regionname
            )
            cls._countriesdata["regionnames2codes"][intermediate_regionname.upper()] = (
                intermediate_regionid
            )
        currency = country.get("Currency")
        cls._countriesdata["currencies"][iso3] = currency
        return country

    @classmethod
    def set_countriesdata(cls, countries: Iterator[dict]) -> None:
        """
        Set up countries data from OCHA countries and territories dataset

        Args:
            countries: Countries data from countries and territories dataset

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
            cls._countriesdata["countrynames2iso3"][key.upper()] = value.upper()

        for country in countries:
            iso3 = country.get("ISO 3166-1 Alpha 3-Codes")
            if not iso3:
                if cls._include_unofficial:
                    iso3 = country.get("x Alpha3 codes")
                    if not iso3:
                        continue
                else:
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
        include_unofficial: bool | None = None,
        use_live: bool | None = None,
        country_name_overrides: dict | None = None,
        country_name_mappings: dict | None = None,
        downloader: BaseDownload | None = None,
    ) -> list[dict[str, dict]]:
        """
        Read countries data from OCHA countries feed (falling back to file).
        include_unofficial, use_live, country_name_overrides and country_name_mappings
        are taken from internal defaults if they are None, otherwise the internal
        defaults are overridden.

        Args:
            include_unofficial: Include unofficial country alpha codes. Defaults to False.
            use_live: Try to get latest data from web rather than file in package. Defaults to True.
            country_name_overrides: Dictionary of mappings from iso3 to country name
            country_name_mappings: Dictionary of mappings from country name to iso3
            downloader: Download or Retrieve object. Defaults to None.

        Returns:
            Countries dictionaries
        """
        if include_unofficial is not None:
            cls._include_unofficial = include_unofficial
        if use_live is not None:
            cls._use_live = use_live
        if cls._countriesdata is None:
            countries = None
            if country_name_overrides is not None:
                cls.set_country_name_overrides(country_name_overrides)
            if country_name_mappings is not None:
                cls.set_country_name_mappings(country_name_mappings)
            if downloader is None:
                downloader = Download(user_agent="HDXPythonCountry")
            if cls._use_live:
                try:
                    _, countries = downloader.get_tabular_rows(
                        cls._ochaurl, dict_form=True
                    )
                except DownloadError:
                    countries = None
                    logger.warning(
                        f"Download of {cls._ochaurl} failed. Will use internal static file."
                    )
            if countries is None:
                _, countries = downloader.get_tabular_rows(
                    cls._ochapath, dict_form=True
                )
            cls.set_countriesdata(countries)
        return cls._countriesdata

    @classmethod
    def set_include_unofficial_default(
        cls, include_unofficial: bool | None = None
    ) -> None:
        """
        Set the default for include_unofficial which defines if unofficial alpha2 and
        alpha3 codes such as AN and XKX will be included.

        Args:
            include_unofficial: Default value to use for include_unofficial. Defaults to internal value (False).

        Returns:
            None
        """
        if include_unofficial is None:
            include_unofficial = cls._include_unofficial
        cls._include_unofficial = include_unofficial

    @classmethod
    def set_use_live_default(cls, use_live: bool | None = None) -> None:
        """
        Set the default for use_live which defines if latest data is obtained
        from the web rather than taking data from a static file in the package.

        Args:
            use_live: Default value to use for use_live. Defaults to internal value (True).

        Returns:
            None
        """
        if use_live is None:
            use_live = cls._use_live_default
        cls._use_live = use_live

    @classmethod
    def set_ocha_url(cls, url: str = None) -> None:
        """
        Set OCHA url from which to retrieve countries data

        Args:
            url: OCHA url from which to retrieve countries data. Defaults to internal value.

        Returns:
            None
        """
        if url is None:
            url = cls._ochaurl_default
        cls._ochaurl = url

    @classmethod
    def set_ocha_path(cls, path: Path | str | None = None) -> None:
        """
        Set local path from which to retrieve OCHA countries data

        Args:
            path: Local path from which to retrieve countries data. Defaults to None.

        Returns:
            None
        """
        if not path or (path and not os.path.exists(path)):
            path = cls._ochapath_default
        cls._ochapath = path

    @classmethod
    def set_country_name_overrides(cls, country_name_overrides: dict) -> None:
        """
        Setup name overrides using dictionary of mappings from iso3 to country name

        Args:
            country_name_overrides: Dictionary of mappings from iso3 to country name

        Returns:
            None
        """
        cls._country_name_overrides = country_name_overrides

    @classmethod
    def set_country_name_mappings(cls, country_name_mappings: dict) -> None:
        """
        Setup additional name mappings using dictionary of mappings from country name to iso3

        Args:
            country_name_mappings: Dictionary of mappings from country name to iso3

        Returns:
            None
        """
        cls._country_name_mappings = country_name_mappings

    @classmethod
    def get_country_info_from_iso3(
        cls,
        iso3: str,
        use_live: bool = None,
        exception: Exception | None = None,
        downloader: BaseDownload | None = None,
    ) -> dict[str, str] | None:
        """Get country information from ISO3 code

        Args:
            iso3: ISO3 code for which to get country information
            use_live: Try to get use latest data from web rather than file in package. Defaults to True.
            exception: An exception to raise if country not found. Defaults to None.
            downloader: Download or Retrieve object. Defaults to None.

        Returns:
            country information
        """
        countriesdata = cls.countriesdata(use_live=use_live, downloader=downloader)
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
        use_live: bool = None,
        exception: Exception | None = None,
        formal: bool = False,
        downloader: BaseDownload | None = None,
    ) -> str | None:
        """Get country name from ISO3 code

        Args:
            iso3: ISO3 code for which to get country name
            use_live: Try to get use latest data from web rather than file in package. Defaults to True.
            exception: An exception to raise if country not found. Defaults to None.
            formal: Return preferred name if False, formal name if True. Defaults to False.
            downloader: Download or Retrieve object. Defaults to None.

        Returns:
            Country name
        """
        countryinfo = cls.get_country_info_from_iso3(
            iso3, use_live=use_live, exception=exception, downloader=downloader
        )
        if countryinfo is not None:
            countryname = countryinfo.get("Name Override")
            if countryname is not None:
                return countryname
            if formal:
                countryname = countryinfo.get("English Formal")
                if countryname is None or countryname == "":
                    countryname = countryinfo.get("Preferred Term")
                return countryname
            else:
                return countryinfo.get("Preferred Term")
        return None

    @classmethod
    def get_currency_from_iso3(
        cls,
        iso3: str,
        use_live: bool = None,
        exception: Exception | None = None,
        downloader: BaseDownload | None = None,
    ) -> int | None:
        """Get currency code from ISO3 code

        Args:
            iso3: ISO3 code for which to get M49 code
            use_live: Try to get use latest data from web rather than file in package. Defaults to True.
            exception: An exception to raise if country not found. Defaults to None.
            downloader: Download or Retrieve object. Defaults to None.

        Returns:
            Currency code
        """
        countriesdata = cls.countriesdata(use_live=use_live, downloader=downloader)
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
        use_live: bool = None,
        exception: Exception | None = None,
        downloader: BaseDownload | None = None,
    ) -> str | None:
        """Get ISO2 from ISO3 code

        Args:
            iso3: ISO3 code for which to get ISO2 code
            use_live: Try to get use latest data from web rather than file in package. Defaults to True.
            exception: An exception to raise if country not found. Defaults to None.
            downloader: Download or Retrieve object. Defaults to None.

        Returns:
            ISO2 code
        """
        countriesdata = cls.countriesdata(use_live=use_live, downloader=downloader)
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
        use_live: bool = None,
        exception: Exception | None = None,
        downloader: BaseDownload | None = None,
    ) -> str | None:
        """Get ISO3 from ISO2 code

        Args:
            iso2: ISO2 code for which to get ISO3 code
            use_live: Try to get use latest data from web rather than file in package. Defaults to True.
            exception: An exception to raise if country not found. Defaults to None.
            downloader: Download or Retrieve object. Defaults to None.

        Returns:
            ISO3 code
        """
        countriesdata = cls.countriesdata(use_live=use_live, downloader=downloader)
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
        use_live: bool = None,
        exception: Exception | None = None,
        downloader: BaseDownload | None = None,
    ) -> dict[str, str] | None:
        """Get country name from ISO2 code

        Args:
            iso2: ISO2 code for which to get country information
            use_live: Try to get use latest data from web rather than file in package. Defaults to True.
            exception: An exception to raise if country not found. Defaults to None.
            downloader: Download or Retrieve object. Defaults to None.

        Returns:
            Country information
        """
        iso3 = cls.get_iso3_from_iso2(
            iso2, use_live=use_live, exception=exception, downloader=downloader
        )
        if iso3 is not None:
            return cls.get_country_info_from_iso3(
                iso3, use_live=use_live, exception=exception, downloader=downloader
            )
        return None

    @classmethod
    def get_country_name_from_iso2(
        cls,
        iso2: str,
        use_live: bool = None,
        exception: Exception | None = None,
        formal: bool = False,
        downloader: BaseDownload | None = None,
    ) -> str | None:
        """Get country name from ISO2 code

        Args:
            iso2: ISO2 code for which to get country name
            use_live: Try to get use latest data from web rather than file in package. Defaults to True.
            exception: An exception to raise if country not found. Defaults to None.
            formal: Return preferred name if False, formal name if True. Defaults to False.
            downloader: Download or Retrieve object. Defaults to None.

        Returns:
            Country name
        """
        iso3 = cls.get_iso3_from_iso2(
            iso2, use_live=use_live, exception=exception, downloader=downloader
        )
        if iso3 is not None:
            return cls.get_country_name_from_iso3(
                iso3, exception=exception, formal=formal, downloader=downloader
            )
        return None

    @classmethod
    def get_currency_from_iso2(
        cls,
        iso2: str,
        use_live: bool = None,
        exception: Exception | None = None,
        downloader: BaseDownload | None = None,
    ) -> str | None:
        """Get currency from ISO2 code

        Args:
            iso2: ISO2 code for which to get country information
            use_live: Try to get use latest data from web rather than file in package. Defaults to True.
            exception: An exception to raise if country not found. Defaults to None.
            downloader: Download or Retrieve object. Defaults to None.

        Returns:
            Currency
        """
        iso3 = cls.get_iso3_from_iso2(
            iso2, use_live=use_live, exception=exception, downloader=downloader
        )
        if iso3 is not None:
            return cls.get_currency_from_iso3(
                iso3, use_live=use_live, exception=exception, downloader=downloader
            )
        return None

    @classmethod
    def get_m49_from_iso3(
        cls,
        iso3: str,
        use_live: bool = None,
        exception: Exception | None = None,
        downloader: BaseDownload | None = None,
    ) -> int | None:
        """Get M49 from ISO3 code

        Args:
            iso3: ISO3 code for which to get M49 code
            use_live: Try to get use latest data from web rather than file in package. Defaults to True.
            exception: An exception to raise if country not found. Defaults to None.
            downloader: Download or Retrieve object. Defaults to None.

        Returns:
            M49 code
        """
        countriesdata = cls.countriesdata(use_live=use_live, downloader=downloader)
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
        use_live: bool = None,
        exception: Exception | None = None,
        downloader: BaseDownload | None = None,
    ) -> str | None:
        """Get ISO3 from M49 code

        Args:
            m49: M49 numeric code for which to get ISO3 code
            use_live: Try to get use latest data from web rather than file in package. Defaults to True.
            exception: An exception to raise if country not found. Defaults to None.
            downloader: Download or Retrieve object. Defaults to None.

        Returns:
            ISO3 code
        """
        countriesdata = cls.countriesdata(use_live=use_live, downloader=downloader)
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
        use_live: bool = None,
        exception: Exception | None = None,
        downloader: BaseDownload | None = None,
    ) -> dict[str, str] | None:
        """Get country name from M49 code

        Args:
            m49: M49 numeric code for which to get country information
            use_live: Try to get use latest data from web rather than file in package. Defaults to True.
            exception: An exception to raise if country not found. Defaults to None.
            downloader: Download or Retrieve object. Defaults to None.

        Returns:
            Country information
        """
        iso3 = cls.get_iso3_from_m49(
            m49, use_live=use_live, exception=exception, downloader=downloader
        )
        if iso3 is not None:
            return cls.get_country_info_from_iso3(
                iso3, exception=exception, downloader=downloader
            )
        return None

    @classmethod
    def get_country_name_from_m49(
        cls,
        m49: int,
        use_live: bool = None,
        exception: Exception | None = None,
        formal: bool = False,
        downloader: BaseDownload | None = None,
    ) -> str | None:
        """Get country name from M49 code

        Args:
            m49: M49 numeric code for which to get country name
            use_live: Try to get use latest data from web rather than file in package. Defaults to True.
            exception: An exception to raise if country not found. Defaults to None.
            formal: Return preferred name if False, formal name if True. Defaults to False.
            downloader: Download or Retrieve object. Defaults to None.

        Returns:
            Country name
        """
        iso3 = cls.get_iso3_from_m49(
            m49, use_live=use_live, exception=exception, downloader=downloader
        )
        if iso3 is not None:
            return cls.get_country_name_from_iso3(
                iso3, exception=exception, formal=formal, downloader=downloader
            )
        return None

    @classmethod
    def get_currency_from_m49(
        cls,
        m49: int,
        use_live: bool = None,
        exception: Exception | None = None,
        downloader: BaseDownload | None = None,
    ) -> str | None:
        """Get currency from M49 code

        Args:
            m49: M49 numeric code for which to get country name
            use_live: Try to get use latest data from web rather than file in package. Defaults to True.
            exception: An exception to raise if country not found. Defaults to None.
            downloader: Download or Retrieve object. Defaults to None.

        Returns:
            Currency
        """
        iso3 = cls.get_iso3_from_m49(
            m49, use_live=use_live, exception=exception, downloader=downloader
        )
        if iso3 is not None:
            return cls.get_currency_from_iso3(
                iso3, use_live=use_live, exception=exception, downloader=downloader
            )
        return None

    @classmethod
    def expand_countryname_abbrevs(cls, country: str) -> list[str]:
        """Expands abbreviation(s) in country name in various ways (eg. FED -> FEDERATED, FEDERAL etc.)

        Args:
            country: Country with abbreviation(s)to expand

        Returns:
            Uppercase country name with abbreviation(s) expanded in various ways
        """

        def replace_ensure_space(word, replace, replacement):
            return word.replace(replace, f"{replacement} ").replace("  ", " ").strip()

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
                        replace_ensure_space(countryupper, abbreviation, expanded)
                    )
        return candidates

    @classmethod
    def simplify_countryname(cls, country: str) -> tuple[str, list[str]]:
        """Simplifies country name by removing descriptive text eg. DEMOCRATIC, REPUBLIC OF etc.

        Args:
            country: Country name to simplify

        Returns:
            Uppercase simplified country name and list of removed words
        """
        # Convert the input into an upper-cased list of words
        countryupper = country.upper().strip()
        words = get_words_in_sentence(countryupper)

        # Strip common patterns
        index = countryupper.find(",")
        if index != -1:
            countryupper = countryupper[:index]
        index = countryupper.find(":")
        if index != -1:
            countryupper = countryupper[:index]

        if countryupper and not (countryupper[0] == "(" and countryupper[-1] == ")"):
            regex = re.compile(r"\(.+?\)")
            countryupper = regex.sub("", countryupper)

        # Find the words that remain as candidates for the simplified name.
        # These are guaranteed to be a subset of `words` because we have only pruned
        # parts from the sentence and not done any transformative processing.
        candidate_words = get_words_in_sentence(countryupper)

        if candidate_words:
            # Make the simplifying terms indexable for efficient lookup
            multiword_terms = {}
            singleword_terms = set()

            for terms in [
                cls.simplifications,
                cls.abbreviations.keys(),
                cls.abbreviations.values(),
                cls.multiple_abbreviations.keys(),
            ] + list(cls.multiple_abbreviations.values()):
                for term in terms:
                    if " " in term:
                        # Index multi-word terms by the first term against a list of the terms
                        term_parts = term.split(" ")
                        multiword_terms[term_parts[0]] = term_parts
                    else:
                        # Add single word terms to the set, and add their dot-less form as well
                        singleword_terms.add(term)
                        if term[-1] == ".":
                            singleword_terms.add(term.strip("."))

            num_candidate_words = len(candidate_words)
            simplified_term = ""
            enumerated_words = enumerate(candidate_words)
            default = (num_candidate_words, "")

            # Iterate through the candidate terms until we a) find a non-simplified word
            # or b) hit the end of the list of words
            while (val := next(enumerated_words, default)) != default:
                i, word = val
                if word in singleword_terms:
                    # If the word was a single word simplification term then skip it
                    continue
                if (
                    # If the current term is the first word in a multi-part term
                    (term_parts := multiword_terms.get(word))
                    # And there are enough words left in the sentence
                    and i + len(term_parts) <= num_candidate_words
                    # And all of the words in the multi-word phrase are in sequence
                    # in the candidate term starting at the current position
                    and all(
                        candidate_words[i + j] == term_part
                        for j, term_part in enumerate(term_parts)
                    )
                ):
                    # Then skip the other words in the term and continue
                    for _ in range(len(term_parts) - 1):
                        next(enumerated_words)

                    continue
                # Else we found a word that we aren't dropping - it is our simplified word.
                # Take it and break.
                simplified_term = word
                break

            if simplified_term:
                # We found a simplified term. Remove it from the list of other terms
                words.remove(simplified_term)
        else:
            simplified_term = ""

        return simplified_term, words

    @classmethod
    def get_iso3_country_code(
        cls,
        country: str,
        use_live: bool = None,
        exception: Exception | None = None,
        downloader: BaseDownload | None = None,
    ) -> str | None:
        """Get ISO3 code for cls. Only exact matches or None are returned.

        Args:
            country: Country for which to get ISO3 code
            use_live: Try to get use latest data from web rather than file in package. Defaults to True.
            exception: An exception to raise if country not found. Defaults to None.
            downloader: Download or Retrieve object. Defaults to None.

        Returns:
            ISO3 country code or None
        """
        countriesdata = cls.countriesdata(use_live=use_live, downloader=downloader)
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
                if countriesdata["countries"][country]["Chinese Short"] == countryupper:
                    return country
        elif re.search(r"[\u0600-\u06FF]+", countryupper):
            for country in countriesdata["countries"]:
                if countriesdata["countries"][country]["Arabic Short"] == countryupper:
                    return country

        if exception is not None:
            raise exception
        return None

    @classmethod
    def get_iso3_country_code_fuzzy(
        cls,
        country: str,
        use_live: bool = None,
        exception: Exception | None = None,
        min_chars: int = 5,
        downloader: BaseDownload | None = None,
    ) -> tuple[str | None, bool]:
        """Get ISO3 code for cls. A tuple is returned with the first value being the ISO3 code and the second
        showing if the match is exact or not.

        Args:
            country: Country for which to get ISO3 code
            use_live: Try to get use latest data from web rather than file in package. Defaults to True.
            exception: An exception to raise if country not found. Defaults to None.
            min_chars: Minimum number of characters for fuzzy matching to be tried. Defaults to 5.
            downloader: Download or Retrieve object. Defaults to None.

        Returns:
            ISO3 code and if the match is exact or (None, False).
        """
        countriesdata = cls.countriesdata(use_live=use_live, downloader=downloader)
        country = country.strip()
        if not country.upper().isupper():
            return None, False

        iso3 = cls.get_iso3_country_code(
            country, use_live=use_live, downloader=downloader
        )
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
                simplified_country, removed_words = cls.simplify_countryname(candidate)
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
        region: int | str,
        use_live: bool = None,
        exception: Exception | None = None,
        downloader: BaseDownload | None = None,
    ) -> list[str]:
        """Get countries (ISO3 codes) in region

        Args:
            region: Three digit UNStats M49 region code or region name
            use_live: Try to get use latest data from web rather than file in package. Defaults to True.
            exception: An exception to raise if region not found. Defaults to None.
            downloader: Download or Retrieve object. Defaults to None.

        Returns:
            Sorted list of ISO3 country names
        """
        countriesdata = cls.countriesdata(use_live=use_live, downloader=downloader)
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

    @classmethod
    def get_hrp_status_from_iso3(
        cls,
        iso3: str,
        use_live: bool = None,
        exception: Exception | None = None,
        downloader: BaseDownload | None = None,
    ) -> bool | None:
        """Get HRP status from ISO3 code

        Args:
            iso3: ISO3 code for which to get M49 code
            use_live: Try to get use latest data from web rather than file in package. Defaults to True.
            exception: An exception to raise if country not found. Defaults to None.
            downloader: Download or Retrieve object. Defaults to None.

        Returns:
            Has HRP (True, False or None)
        """
        countryinfo = cls.get_country_info_from_iso3(
            iso3, use_live=use_live, exception=exception, downloader=downloader
        )
        if not countryinfo:
            return None
        return countryinfo.get("Has HRP") == "Y"

    @classmethod
    def get_gho_status_from_iso3(
        cls,
        iso3: str,
        use_live: bool = None,
        exception: Exception | None = None,
        downloader: BaseDownload | None = None,
    ) -> bool | None:
        """Get GHO status from ISO3 code

        Args:
            iso3: ISO3 code for which to get M49 code
            use_live: Try to get use latest data from web rather than file in package. Defaults to True.
            exception: An exception to raise if country not found. Defaults to None.
            downloader: Download or Retrieve object. Defaults to None.

        Returns:
            In GHO (True, False or None)
        """
        countryinfo = cls.get_country_info_from_iso3(
            iso3, use_live=use_live, exception=exception, downloader=downloader
        )
        if not countryinfo:
            return None
        return countryinfo.get("In GHO") == "Y"
