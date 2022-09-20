import logging
from typing import Dict, List, Optional, Tuple

from hdx.utilities.text import multiple_replace
from unidecode import unidecode

from hdx.location.country import Country
from hdx.location.names import clean_name
from hdx.location.phonetics import Phonetics

logger = logging.getLogger(__name__)


class AdminLevel:
    """AdminLevel class which takes in pcodes and then maps names to those pcodes with fuzzy matching if necessary. The
    input configuration dictionary, admin_config, requires key admin_info which is a list with values of the form:
    ::
        {"iso3": "AFG", "pcode": "AF01", "name": "Kabul"}

    Various other keys are optional:
    countries_fuzzy_try are countries (iso3 codes) for which to try fuzzy matching. Default is all countries.
    admin_name_mappings is a dictionary of mappings from name to pcode (for where fuzzy matching fails)
    admin_name_replacements is a dictionary of textual replacements to try when fuzzy matching
    admin_fuzzy_dont is a list of names for which fuzzy matching should not be tried

    Args:
        admin_config (Dict): Configuration dictionary
        admin_level (int): Admin level. Defaults to 1.
        admin_level_overrides (Dict): Countries at other admin levels.
    """

    def __init__(
        self,
        admin_config: Dict,
        admin_level: int = 1,
        admin_level_overrides: Dict = dict(),
    ) -> None:
        admin_info = admin_config["admin_info"]
        self.admin_level = admin_level
        self.admin_level_overrides = admin_level_overrides
        self.countries_fuzzy_try = admin_config.get("countries_fuzzy_try")
        self.admin_name_mappings = admin_config.get(
            "admin_name_mappings", dict()
        )
        self.admin_name_replacements = admin_config.get(
            "admin_name_replacements", dict()
        )
        self.admin_fuzzy_dont = admin_config.get("admin_fuzzy_dont", list())
        self.pcodes = list()
        self.pcode_lengths = dict()
        self.name_to_pcode = dict()
        self.pcode_to_name = dict()
        self.pcode_to_iso3 = dict()

        for row in admin_info:
            countryiso3 = row["iso3"]
            pcode = row.get("pcode")
            self.pcodes.append(pcode)
            self.pcode_lengths[countryiso3] = len(pcode)
            adm_name = row["name"]
            self.pcode_to_name[pcode] = adm_name
            name_to_pcode = self.name_to_pcode.get(countryiso3, dict())
            name_to_pcode[unidecode(adm_name).lower()] = pcode
            self.name_to_pcode[countryiso3] = name_to_pcode
            self.pcode_to_iso3[pcode] = countryiso3
        self.init_matches_errors()
        self.phonetics = Phonetics()

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
