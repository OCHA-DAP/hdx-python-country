import logging
from typing import Dict, List, Optional, Tuple

import hxl
from hxl import InputOptions
from hxl.input import HXLIOException
from unidecode import unidecode

from hdx.location.country import Country
from hdx.location.names import clean_name
from hdx.location.phonetics import Phonetics
from hdx.utilities.text import multiple_replace
from hdx.utilities.typehint import ListTuple

logger = logging.getLogger(__name__)


class AdminLevel:
    """AdminLevel class which takes in p-codes and then maps names to those
    p-codes with fuzzy matching if necessary.

    The dictionary admin_config, which defaults to an empty dictionary, can
    have the following optional keys:
    countries_fuzzy_try are countries (iso3 codes) for which to try fuzzy
    matching. Default is all countries.
    admin_name_mappings is a dictionary of mappings from name to p-code (for
    where fuzzy matching fails)
    admin_name_replacements is a dictionary of textual replacements to try when
    fuzzy matching
    admin_fuzzy_dont is a list of names for which fuzzy matching should not be
    tried

    Args:
        admin_config (Dict): Configuration dictionary. Defaults to {}.
        admin_level (int): Admin level. Defaults to 1.
        admin_level_overrides (Dict): Countries at other admin levels.
    """

    _admin_url_default = "https://data.humdata.org/dataset/cb963915-d7d1-4ffa-90dc-31277e24406f/resource/f65bc260-4d8b-416f-ac07-f2433b4d5142/download/global_pcodes_adm_1_2.csv"
    _admin_url = _admin_url_default

    def __init__(
        self,
        admin_config: Dict = {},
        admin_level: int = 1,
        admin_level_overrides: Dict = {},
    ) -> None:
        self.admin_level = admin_level
        self.admin_level_overrides = admin_level_overrides
        self.countries_fuzzy_try = admin_config.get("countries_fuzzy_try")
        self.admin_name_mappings = admin_config.get("admin_name_mappings", {})
        self.admin_name_replacements = admin_config.get(
            "admin_name_replacements", {}
        )
        self.admin_fuzzy_dont = admin_config.get("admin_fuzzy_dont", list())
        self.pcodes = list()
        self.pcode_lengths = {}
        self.name_to_pcode = {}
        self.pcode_to_name = {}
        self.pcode_to_iso3 = {}

        self.init_matches_errors()
        self.phonetics = Phonetics()

    @classmethod
    def set_default_admin_url(cls, admin_url: Optional[str] = None) -> None:
        """
        Set default admin URL from which to retrieve admin data

        Args:
            admin_url (Optional[str]): Admin URL from which to retrieve admin data. Defaults to internal value.

        Returns:
            None
        """
        if admin_url is None:
            admin_url = cls._admin_url_default
        cls._admin_url = admin_url

    @classmethod
    def get_libhxl_dataset(cls, admin_url: str = _admin_url) -> hxl.Dataset:
        """
        Get libhxl Dataset object given a URL which defaults to global p-codes
        dataset on HDX.

        Args:
            admin_url (str): URL from which to load data. Defaults to global p-codes dataset.

        Returns:
            None
        """
        try:
            return hxl.data(admin_url, InputOptions(encoding="utf-8"))
        except HXLIOException:
            logger.exception(
                f"Setup of libhxl Dataset object with {admin_url} failed!"
            )
            raise

    def setup_from_admin_info(self, admin_info: ListTuple[Dict]) -> None:
        """
        Setup p-codes from admin_info which is a list with values of the form:
        ::
            {"iso3": "AFG", "pcode": "AF01", "name": "Kabul"}
        Args:
            admin_info (ListTuple[Dict]): p-code dictionary

        Returns:
            None
        """
        for row in admin_info:
            countryiso3 = row["iso3"]
            pcode = row.get("pcode")
            self.pcodes.append(pcode)
            self.pcode_lengths[countryiso3] = len(pcode)
            adm_name = row["name"]
            self.pcode_to_name[pcode] = adm_name
            name_to_pcode = self.name_to_pcode.get(countryiso3, {})
            name_to_pcode[unidecode(adm_name).lower()] = pcode
            self.name_to_pcode[countryiso3] = name_to_pcode
            self.pcode_to_iso3[pcode] = countryiso3

    def setup_from_libhxl_dataset(self, libhxl_dataset: hxl.Dataset) -> None:
        """
        Setup p-codes from a libhxl Dataset object.

        Args:
            libhxl_dataset (hxl.Dataset): Dataset object from libhxl library

        Returns:
            None
        """
        admin_info = libhxl_dataset.with_rows(
            f"#geo+admin_level={self.admin_level}"
        )
        for row in admin_info:
            countryiso3 = row.get("#country+code")
            pcode = row.get("#adm+code")
            self.pcodes.append(pcode)
            self.pcode_lengths[countryiso3] = len(pcode)
            adm_name = row.get("#adm+name")
            self.pcode_to_name[pcode] = adm_name
            name_to_pcode = self.name_to_pcode.get(countryiso3, {})
            name_to_pcode[unidecode(adm_name).lower()] = pcode
            self.name_to_pcode[countryiso3] = name_to_pcode
            self.pcode_to_iso3[pcode] = countryiso3

    def setup_from_url(self, admin_url: str = _admin_url) -> None:
        """
        Setup p-codes from a URL. Defaults to global p-codes dataset on HDX.

        Args:
            admin_url (str): URL from which to load data. Defaults to global p-codes dataset.

        Returns:
            None
        """
        admin_info = self.get_libhxl_dataset(admin_url)
        self.setup_from_libhxl_dataset(admin_info)

    def get_pcode_list(self) -> List[str]:
        """Get list of all pcodes

        Returns:
            List[str]: List of pcodes
        """
        return self.pcodes

    def get_admin_level(self, countryiso3: str) -> int:
        """Get admin level for country

        Args:
            countryiso3 (str): Iso3 country code

        Returns:
            int: Admin level
        """
        admin_level = self.admin_level_overrides.get(countryiso3)
        if admin_level:
            return admin_level
        return self.admin_level

    def get_pcode_length(self, countryiso3: str) -> Optional[int]:
        """Get pcode length for country

        Args:
            countryiso3 (str): Iso3 country code

        Returns:
            Optional[int]: Country's pcode length or None
        """
        return self.pcode_lengths.get(countryiso3)

    def init_matches_errors(self) -> None:
        """Initialise storage of fuzzy matches, ignored and errors for logging purposes

        Returns:
            None
        """

        self.matches = set()
        self.ignored = set()
        self.errors = set()

    def convert_admin1_pcode_length(
        self, countryiso3: str, pcode: str, logname: Optional[str] = None
    ) -> Optional[str]:
        """Standardise pcode length by country and match to an internal pcode. Only
        works for admin1 pcodes.

        Args:
            countryiso3 (str): Iso3 country code
            pcode (str): P code for admin one
            logname (Optional[str]): Identifying name to use when logging. Defaults to None (don't log).

        Returns:
            Optional[str]: Matched P code or None if no match
        """
        pcode_length = len(pcode)
        country_pcodelength = self.pcode_lengths.get(countryiso3)
        if not country_pcodelength:
            return None
        if (
            pcode_length == country_pcodelength
            or pcode_length < 4
            or pcode_length > 6
        ):
            return None
        if country_pcodelength == 4:
            pcode = f"{Country.get_iso2_from_iso3(pcode[:3])}{pcode[-2:]}"
        elif country_pcodelength == 5:
            if pcode_length == 4:
                pcode = f"{pcode[:2]}0{pcode[-2:]}"
            else:
                pcode = f"{Country.get_iso2_from_iso3(pcode[:3])}{pcode[-3:]}"
        elif country_pcodelength == 6:
            if pcode_length == 4:
                pcode = f"{Country.get_iso3_from_iso2(pcode[:2])}0{pcode[-2:]}"
            else:
                pcode = f"{Country.get_iso3_from_iso2(pcode[:2])}{pcode[-3:]}"
        else:
            pcode = None
        if pcode in self.pcodes:
            if logname:
                self.matches.add(
                    (
                        logname,
                        countryiso3,
                        pcode,
                        self.pcode_to_name[pcode],
                        "pcode length conversion",
                    )
                )
            return pcode
        return None

    def fuzzy_pcode(
        self, countryiso3: str, name: str, logname: Optional[str] = None
    ) -> Optional[str]:
        """Fuzzy match name to pcode

        Args:
            countryiso3 (str): Iso3 country code
            name (str): Name to match
            logname (Optional[str]): Identifying name to use when logging. Defaults to None (don't log).

        Returns:
            Optional[str]: Matched P code or None if no match
        """
        if (
            self.countries_fuzzy_try is not None
            and countryiso3 not in self.countries_fuzzy_try
        ):
            if logname:
                self.ignored.add((logname, countryiso3))
            return None
        name_to_pcode = self.name_to_pcode.get(countryiso3)
        if not name_to_pcode:
            if logname:
                self.errors.add((logname, countryiso3))
            return None
        adm_name_lookup = clean_name(name)
        adm_name_lookup2 = multiple_replace(
            adm_name_lookup, self.admin_name_replacements
        )
        pcode = name_to_pcode.get(
            adm_name_lookup, name_to_pcode.get(adm_name_lookup2)
        )
        if not pcode and name.lower() in self.admin_fuzzy_dont:
            if logname:
                self.ignored.add((logname, countryiso3, name))
            return None
        if not pcode:
            for map_name in name_to_pcode:
                if adm_name_lookup in map_name:
                    pcode = name_to_pcode[map_name]
                    if logname:
                        self.matches.add(
                            (
                                logname,
                                countryiso3,
                                name,
                                self.pcode_to_name[pcode],
                                "substring",
                            )
                        )
                    break
            for map_name in name_to_pcode:
                if adm_name_lookup2 in map_name:
                    pcode = name_to_pcode[map_name]
                    if logname:
                        self.matches.add(
                            (
                                logname,
                                countryiso3,
                                name,
                                self.pcode_to_name[pcode],
                                "substring",
                            )
                        )
                    break
        if not pcode:
            map_names = list(name_to_pcode.keys())
            lower_mapnames = [x.lower() for x in map_names]

            def al_transform_1(name):
                if name[:3] == "al ":
                    return f"ad {name[3:]}"
                else:
                    return None

            def al_transform_2(name):
                if name[:3] == "al ":
                    return name[3:]
                else:
                    return None

            matching_index = self.phonetics.match(
                lower_mapnames,
                adm_name_lookup,
                alternative_name=adm_name_lookup2,
                transform_possible_names=[al_transform_1, al_transform_2],
            )

            if matching_index is None:
                if logname:
                    self.errors.add((logname, countryiso3, name))
                return None

            map_name = map_names[matching_index]
            pcode = name_to_pcode[map_name]
            if logname:
                self.matches.add(
                    (
                        logname,
                        countryiso3,
                        name,
                        self.pcode_to_name[pcode],
                        "fuzzy",
                    )
                )
        return pcode

    def get_pcode(
        self,
        countryiso3: str,
        name: str,
        fuzzy_match: bool = True,
        logname: Optional[str] = None,
    ) -> Tuple[Optional[str], bool]:
        """Get pcode for a given name

        Args:
            countryiso3 (str): Iso3 country code
            name (str): Name to match
            fuzzy_match (bool): Whether to try fuzzy matching. Defaults to True.
            logname (Optional[str]): Identifying name to use when logging. Defaults to None (don't log).

        Returns:
            Tuple[Optional[str], bool]: (Matched P code or None if no match, True if exact match or False if not)
        """
        pcode = self.admin_name_mappings.get(name)
        if pcode and self.pcode_to_iso3[pcode] == countryiso3:
            return pcode, True
        name_to_pcode = self.name_to_pcode.get(countryiso3)
        if name_to_pcode is not None:
            pcode = name_to_pcode.get(name.lower())
            if pcode:
                return pcode, True
        if name in self.pcodes:  # name is a pcode
            return name, True
        if self.get_admin_level(countryiso3) == 1:
            pcode = self.convert_admin1_pcode_length(
                countryiso3, name, logname
            )
            if pcode:
                return pcode, True
        if not fuzzy_match:
            return None, True
        pcode = self.fuzzy_pcode(countryiso3, name, logname)
        return pcode, False

    def output_matches(self) -> List[str]:
        """Output log of matches

        Returns:
            List[str]: List of matches
        """
        output = list()
        for match in sorted(self.matches):
            line = f"{match[0]} - {match[1]}: Matching ({match[4]}) {match[2]} to {match[3]} on map"
            logger.info(line)
            output.append(line)
        return output

    def output_ignored(self) -> List[str]:
        """Output log of ignored

        Returns:
            List[str]: List of ignored
        """
        output = list()
        for ignored in sorted(self.ignored):
            if len(ignored) == 2:
                line = f"{ignored[0]} - Ignored {ignored[1]}!"
            else:
                line = f"{ignored[0]} - {ignored[1]}: Ignored {ignored[2]}!"
            logger.info(line)
            output.append(line)
        return output

    def output_errors(self) -> List[str]:
        """Output log of errors

        Returns:
            List[str]: List of errors
        """
        output = list()
        for error in sorted(self.errors):
            if len(error) == 2:
                line = f"{error[0]} - Could not find {error[1]} in map names!"
            else:
                line = f"{error[0]} - {error[1]}: Could not find {error[2]} in map names!"
            logger.error(line)
            output.append(line)
        return output
