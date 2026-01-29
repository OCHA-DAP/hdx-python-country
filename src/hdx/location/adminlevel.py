import logging
import re
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import hxl
from hdx.utilities.base_downloader import DownloadError
from hdx.utilities.dictandlist import dict_of_sets_add
from hdx.utilities.matching import Phonetics, multiple_replace
from hdx.utilities.retriever import Retrieve
from hdx.utilities.text import normalise
from hxl import InputOptions
from hxl.input import HXLIOException

from hdx.location.country import Country

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

    The admin_level_overrides parameter allows manually overriding the returned
    admin level for given countries. It is a dictionary with iso3s as keys and
    admin level numbers as values.

    The retriever parameter accepts an object of type Retrieve (or inherited
    classes). It is used to allow either that admin data from urls is saved
    to files or to enable already saved files to be used instead of downloading
    from urls.

    Args:
        admin_config: Configuration dictionary. Defaults to {}.
        admin_level: Admin level. Defaults to 1.
        admin_level_overrides: Countries at other admin levels.
        retriever: Retriever object to use for loading/saving files. Defaults to None.
    """

    pcode_regex = re.compile(r"^([a-zA-Z]{2,3})(\d+)$")
    _admin_url_default = "https://data.humdata.org/dataset/cb963915-d7d1-4ffa-90dc-31277e24406f/resource/f65bc260-4d8b-416f-ac07-f2433b4d5142/download/global_pcodes_adm_1_2.csv"
    admin_url = _admin_url_default
    admin_all_pcodes_url = "https://data.humdata.org/dataset/cb963915-d7d1-4ffa-90dc-31277e24406f/resource/793e66fe-4cdb-4076-b037-fb8c053239e2/download/global_pcodes.csv"
    _formats_url_default = "https://data.humdata.org/dataset/cb963915-d7d1-4ffa-90dc-31277e24406f/resource/f1161807-dab4-4331-b7b0-4e5dac56e0e4/download/global_pcode_lengths.csv"
    formats_url = _formats_url_default

    def __init__(
        self,
        admin_config: dict = {},
        admin_level: int = 1,
        admin_level_overrides: dict = {},
        retriever: Retrieve | None = None,
    ) -> None:
        self.admin_level = admin_level
        self.admin_level_overrides = admin_level_overrides
        self.retriever: Retrieve | None = retriever
        self.countries_fuzzy_try = admin_config.get("countries_fuzzy_try")
        self.admin_name_mappings = admin_config.get("admin_name_mappings", {})
        self.admin_name_replacements = admin_config.get("admin_name_replacements", {})
        self.admin_fuzzy_dont = admin_config.get("admin_fuzzy_dont", list())
        self.pcodes = []
        self.pcode_lengths = {}
        self.name_to_pcode = {}
        self.name_parent_to_pcode = {}
        self.pcode_to_name = {}
        self.pcode_to_iso3 = {}
        self.pcode_to_parent = {}
        self.pcode_formats = {}
        self.use_parent = False
        self.zeroes = {}
        self.parent_admins = []

        self.init_matches_errors()
        self.phonetics = Phonetics()

    @classmethod
    def looks_like_pcode(cls, string: str) -> bool:
        """Check if a string looks like a p-code using regex matching of format.
        Checks for 2 or 3 letter country iso code at start and then numbers.

        Args:
            string: String to check

        Returns:
            Whether string looks like a p-code
        """
        if cls.pcode_regex.match(string):
            return True
        return False

    @classmethod
    def set_default_admin_url(cls, admin_url: str | None = None) -> None:
        """
        Set default admin URL from which to retrieve admin data

        Args:
            admin_url: Admin URL from which to retrieve admin data. Defaults to internal value.

        Returns:
            None
        """
        if admin_url is None:
            admin_url = cls._admin_url_default
        cls.admin_url = admin_url

    @staticmethod
    def get_libhxl_dataset(
        url: Path | str = admin_url, retriever: Retrieve | None = None
    ) -> hxl.Dataset:
        """
        Get libhxl Dataset object given a URL which defaults to global p-codes
        dataset on HDX.

        Args:
            url: URL from which to load data. Defaults to internal admin url.
            retriever: Retriever object to use for loading file. Defaults to None.

        Returns:
            HXL Dataset object
        """
        if retriever:
            try:
                url_to_use = retriever.download_file(url)
            except DownloadError:
                logger.exception(f"Setup of libhxl Dataset object with {url} failed!")
                raise
        else:
            url_to_use = url
        try:
            return hxl.data(
                str(url_to_use),
                InputOptions(InputOptions(allow_local=True, encoding="utf-8")),
            )
        except (FileNotFoundError, HXLIOException):
            logger.exception(f"Setup of libhxl Dataset object with {url} failed!")
            raise

    def setup_row(
        self,
        countryiso3: str,
        pcode: str,
        adm_name: str | None,
        parent: str | None,
    ):
        """
        Setup a single p-code

        Args:
            countryiso3: Country
            pcode: P-code
            adm_name: Administrative name (which can be None)
            parent: Parent p-code

        Returns:
            None
        """
        self.pcode_lengths[countryiso3] = len(pcode)
        self.pcodes.append(pcode)
        if adm_name is None:
            adm_name = ""
        self.pcode_to_name[pcode] = adm_name
        self.pcode_to_iso3[pcode] = countryiso3
        if not adm_name:
            logger.error(f"Admin name is blank for pcode {pcode} of {countryiso3}!")
            return

        adm_name = normalise(adm_name)
        name_to_pcode = self.name_to_pcode.get(countryiso3, {})
        name_to_pcode[adm_name] = pcode
        self.name_to_pcode[countryiso3] = name_to_pcode

        if self.use_parent:
            name_parent_to_pcode = self.name_parent_to_pcode.get(countryiso3, {})
            name_to_pcode = name_parent_to_pcode.get(parent, {})
            name_to_pcode[adm_name] = pcode
            name_parent_to_pcode[parent] = name_to_pcode
            self.name_parent_to_pcode[countryiso3] = name_parent_to_pcode
            self.pcode_to_parent[pcode] = parent

    def setup_from_admin_info(
        self,
        admin_info: Sequence[dict],
        countryiso3s: Sequence[str] | None = None,
    ) -> None:
        """
        Setup p-codes from admin_info which is a list with values of the form
        below with parent optional:
        ::
            {"iso3": "AFG", "pcode": "AF0101", "name": "Kabul", parent: "AF01"}
        Args:
            admin_info: p-code dictionary
            countryiso3s: Countries to read. Defaults to None (all).

        Returns:
            None
        """
        if countryiso3s:
            countryiso3s = [countryiso3.upper() for countryiso3 in countryiso3s]
        self.use_parent = "parent" in admin_info[0]
        for row in admin_info:
            countryiso3 = row["iso3"].upper()
            if countryiso3s and countryiso3 not in countryiso3s:
                continue
            pcode = row.get("pcode").upper()
            adm_name = row["name"]
            parent = row.get("parent")
            self.setup_row(countryiso3, pcode, adm_name, parent)

    def setup_from_libhxl_dataset(
        self,
        libhxl_dataset: hxl.Dataset,
        countryiso3s: Sequence[str] | None = None,
    ) -> None:
        """
        Setup p-codes from a libhxl Dataset object.

        Args:
            libhxl_dataset: Dataset object from libhxl library
            countryiso3s: Countries to read. Defaults to None (all).

        Returns:
            None
        """
        admin_info = libhxl_dataset.with_rows(f"#geo+admin_level={self.admin_level}")
        if countryiso3s:
            countryiso3s = [countryiso3.upper() for countryiso3 in countryiso3s]
        self.use_parent = "#adm+code+parent" in admin_info.display_tags
        for row in admin_info:
            countryiso3 = row.get("#country+code").upper()
            if countryiso3s and countryiso3 not in countryiso3s:
                continue
            pcode = row.get("#adm+code").upper()
            adm_name = row.get("#adm+name")
            parent = row.get("#adm+code+parent")
            self.setup_row(countryiso3, pcode, adm_name, parent)

    def setup_from_url(
        self,
        admin_url: Path | str = admin_url,
        countryiso3s: Sequence[str] | None = None,
    ) -> None:
        """
        Setup p-codes from a URL. Defaults to global p-codes dataset on HDX.

        Args:
            admin_url: URL from which to load data. Defaults to global p-codes dataset.
            countryiso3s: Countries to read. Defaults to None (all).

        Returns:
            None
        """
        admin_info = self.get_libhxl_dataset(admin_url, self.retriever)
        self.setup_from_libhxl_dataset(admin_info, countryiso3s)

    def load_pcode_formats_from_libhxl_dataset(
        self, libhxl_dataset: hxl.Dataset
    ) -> None:
        """
        Load p-code formats from a libhxl Dataset object.

        Args:
            libhxl_dataset: Dataset object from libhxl library

        Returns:
            None
        """
        for row in libhxl_dataset:
            pcode_format = [int(row.get("#country+len"))]
            for admin_no in range(1, 4):
                length = row.get(f"#adm{admin_no}+len")
                if not length or "|" in length:
                    break
                pcode_format.append(int(length))
            self.pcode_formats[row.get("#country+code")] = pcode_format

        for pcode in self.pcodes:
            countryiso3 = self.pcode_to_iso3[pcode]
            for x in re.finditer("0", pcode):
                dict_of_sets_add(self.zeroes, countryiso3, x.start())

    def load_pcode_formats(self, formats_url: Path | str = formats_url) -> None:
        """
        Load p-code formats from a URL. Defaults to global p-codes dataset on HDX.

        Args:
            formats_url: URL from which to load data. Defaults to global p-codes dataset.

        Returns:
            None
        """
        formats_info = self.get_libhxl_dataset(formats_url, self.retriever)
        self.load_pcode_formats_from_libhxl_dataset(formats_info)

    def set_parent_admins(self, parent_admins: list[list]) -> None:
        """
        Set parent admins

        Args:
            parent_admins: List of P-codes per parent admin

        Returns:
            None
        """
        self.parent_admins = parent_admins

    def set_parent_admins_from_adminlevels(
        self, adminlevels: list["AdminLevel"]
    ) -> None:
        """
        Set parent admins from AdminLevel objects

        Args:
            parent_admins: List of parent AdminLevel objects

        Returns:
            None
        """
        self.parent_admins = [adminlevel.pcodes for adminlevel in adminlevels]

    def get_pcode_list(self) -> list[str]:
        """Get list of all pcodes

        Returns:
            List of pcodes
        """
        return self.pcodes

    def get_admin_level(self, countryiso3: str) -> int:
        """Get admin level for country

        Args:
            countryiso3: ISO3 country code

        Returns:
            Admin level
        """
        admin_level = self.admin_level_overrides.get(countryiso3)
        if admin_level:
            return admin_level
        return self.admin_level

    def get_pcode_length(self, countryiso3: str) -> int | None:
        """Get pcode length for country

        Args:
            countryiso3: ISO3 country code

        Returns:
            Country's pcode length or None
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

    def convert_admin_pcode_length(
        self, countryiso3: str, pcode: str, **kwargs: Any
    ) -> str | None:
        """Standardise pcode length by country and match to an internal pcode.
        Requires that p-code formats be loaded (eg. using load_pcode_formats)

        Args:
            countryiso3: ISO3 country code
            pcode: P code to match
            **kwargs: See below
            parent (str): Parent admin code
            logname (str): Log using this identifying name. Defaults to not logging.

        Returns:
            Matched P code or None if no match
        """
        logname = kwargs.get("logname")
        match = self.pcode_regex.match(pcode)
        if not match:
            return None
        pcode_format = self.pcode_formats.get(countryiso3)
        if not pcode_format:
            if self.get_admin_level(countryiso3) == 1:
                return self.convert_admin1_pcode_length(countryiso3, pcode, logname)
            return None
        countryiso, digits = match.groups()
        countryiso_length = len(countryiso)
        if countryiso_length > pcode_format[0]:
            countryiso2 = Country.get_iso2_from_iso3(countryiso3)
            pcode_parts = [countryiso2, digits]
        elif countryiso_length < pcode_format[0]:
            pcode_parts = [countryiso3, digits]
        else:
            pcode_parts = [countryiso, digits]
        new_pcode = "".join(pcode_parts)
        if new_pcode in self.pcodes:
            if logname:
                self.matches.add(
                    (
                        logname,
                        countryiso3,
                        new_pcode,
                        self.pcode_to_name[new_pcode],
                        "pcode length conversion-country",
                    )
                )
            return new_pcode
        total_length = sum(pcode_format[: self.admin_level + 1])
        admin_changes = []
        for admin_no in range(1, self.admin_level + 1):
            len_new_pcode = len(new_pcode)
            if len_new_pcode == total_length:
                break
            admin_length = pcode_format[admin_no]
            pcode_part = pcode_parts[admin_no]
            part_length = len(pcode_part)
            if part_length == admin_length:
                break
            pos = sum(pcode_format[:admin_no])
            if part_length < admin_length:
                if pos in self.zeroes[countryiso3]:
                    pcode_parts[admin_no] = f"0{pcode_part}"
                    admin_changes.append(str(admin_no))
                    new_pcode = "".join(pcode_parts)
                break
            elif part_length > admin_length and admin_no == self.admin_level:
                if pcode_part[0] == "0":
                    pcode_parts[admin_no] = pcode_part[1:]
                    admin_changes.append(str(admin_no))
                    new_pcode = "".join(pcode_parts)
                    break
            if len_new_pcode < total_length:
                if admin_length > 2 and pos in self.zeroes[countryiso3]:
                    pcode_part = f"0{pcode_part}"
                    if self.parent_admins and admin_no < self.admin_level:
                        parent_pcode = [pcode_parts[i] for i in range(admin_no)]
                        parent_pcode.append(pcode_part[:admin_length])
                        parent_pcode = "".join(parent_pcode)
                        if parent_pcode not in self.parent_admins[admin_no - 1]:
                            pcode_part = pcode_part[1:]
                        else:
                            admin_changes.append(str(admin_no))
                    else:
                        admin_changes.append(str(admin_no))
            elif len_new_pcode > total_length:
                if admin_length <= 2 and pcode_part[0] == "0":
                    pcode_part = pcode_part[1:]
                    if self.parent_admins and admin_no < self.admin_level:
                        parent_pcode = [pcode_parts[i] for i in range(admin_no)]
                        parent_pcode.append(pcode_part[:admin_length])
                        parent_pcode = "".join(parent_pcode)
                        if parent_pcode not in self.parent_admins[admin_no - 1]:
                            pcode_part = f"0{pcode_part}"
                        else:
                            admin_changes.append(str(admin_no))
                    else:
                        admin_changes.append(str(admin_no))
            pcode_parts[admin_no] = pcode_part[:admin_length]
            pcode_parts.append(pcode_part[admin_length:])
            new_pcode = "".join(pcode_parts)
        if new_pcode in self.pcodes:
            if logname:
                admin_changes_str = ",".join(admin_changes)
                self.matches.add(
                    (
                        logname,
                        countryiso3,
                        new_pcode,
                        self.pcode_to_name[new_pcode],
                        f"pcode length conversion-admins {admin_changes_str}",
                    )
                )
            return new_pcode
        return None

    def convert_admin1_pcode_length(
        self, countryiso3: str, pcode: str, logname: str | None = None
    ) -> str | None:
        """Standardise pcode length by country and match to an internal pcode.
        Only works for admin1 pcodes.

        Args:
            countryiso3: ISO3 country code
            pcode: P code for admin one to match
            logname: Identifying name to use when logging. Defaults to None (don't log).

        Returns:
            Matched P code or None if no match
        """
        pcode_length = len(pcode)
        country_pcodelength = self.pcode_lengths.get(countryiso3)
        if not country_pcodelength:
            return None
        if pcode_length == country_pcodelength or pcode_length < 4 or pcode_length > 6:
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

    def get_admin_name_replacements(
        self, countryiso3: str, parent: str | None
    ) -> dict[str, str]:
        """Get relevant admin name replacements from admin name replacements
        which is a dictionary of mappings from string to string replacement.
        These can be global or they can be restricted by
        country or parent (if the AdminLevel object has been set up with
        parents). Keys take the form "STRING_TO_REPLACE",
        "AFG|STRING_TO_REPLACE" or "AF01|STRING_TO_REPLACE".

        Args:
            countryiso3: ISO3 country code
            parent: Parent admin code

        Returns:
            Relevant admin name replacements
        """
        relevant_name_replacements = {}
        for key, value in self.admin_name_replacements.items():
            if "|" not in key:
                if key not in relevant_name_replacements:
                    relevant_name_replacements[key] = value
                continue
            prefix, name = key.split("|")
            if parent:
                if prefix == parent:
                    if name not in relevant_name_replacements:
                        relevant_name_replacements[name] = value
                    continue
            if prefix == countryiso3:
                if name not in relevant_name_replacements:
                    relevant_name_replacements[name] = value
                continue
        return relevant_name_replacements

    def get_admin_fuzzy_dont(self, countryiso3: str, parent: str | None) -> list[str]:
        """Get relevant admin names that should not be fuzzy matched from
        admin fuzzy dont which is a list of strings. These can be global
        or they can be restricted by country or parent. Keys take the form
        "DONT_MATCH", "AFG|DONT_MATCH", or "AF01|DONT_MATCH".

        Args:
            countryiso3: ISO3 country code
            parent: Parent admin code

        Returns:
            Relevant admin names that should not be fuzzy matched
        """
        relevant_admin_fuzzy_dont = []
        for value in self.admin_fuzzy_dont:
            if "|" not in value:
                if value not in relevant_admin_fuzzy_dont:
                    relevant_admin_fuzzy_dont.append(value)
                continue
            prefix, name = value.split("|")
            if parent:
                if prefix == parent:
                    if name not in relevant_admin_fuzzy_dont:
                        relevant_admin_fuzzy_dont.append(name)
            if prefix == countryiso3:
                if name not in relevant_admin_fuzzy_dont:
                    relevant_admin_fuzzy_dont.append(name)
                continue
        return relevant_admin_fuzzy_dont

    def fuzzy_pcode(
        self,
        countryiso3: str,
        name: str,
        normalised_name: str,
        **kwargs: Any,
    ) -> str | None:
        """Fuzzy match name to pcode

        Args:
            countryiso3: ISO3 country code
            name: Name to match
            normalised_name: Normalised name
            **kwargs: See below
            parent (str): Parent admin code
            logname (str): Log using this identifying name. Defaults to not logging.

        Returns:
            Matched P code or None if no match
        """
        logname = kwargs.get("logname")
        if (
            self.countries_fuzzy_try is not None
            and countryiso3 not in self.countries_fuzzy_try
        ):
            if logname:
                self.ignored.add((logname, countryiso3))
            return None
        if self.use_parent:
            parent = kwargs.get("parent")
        else:
            parent = None
        if parent is None:
            name_to_pcode = self.name_to_pcode.get(countryiso3)
            if not name_to_pcode:
                if logname:
                    self.errors.add((logname, countryiso3))
                return None
        else:
            name_parent_to_pcode = self.name_parent_to_pcode.get(countryiso3)
            if not name_parent_to_pcode:
                if logname:
                    self.errors.add((logname, countryiso3))
                return None
            name_to_pcode = name_parent_to_pcode.get(parent)
            if not name_to_pcode:
                if logname:
                    self.errors.add((logname, countryiso3, parent))
                return None
        alt_normalised_name = multiple_replace(
            normalised_name,
            self.get_admin_name_replacements(countryiso3, parent),
        )
        pcode = name_to_pcode.get(
            normalised_name, name_to_pcode.get(alt_normalised_name)
        )
        if not pcode and name.lower() in self.get_admin_fuzzy_dont(countryiso3, parent):
            if logname:
                self.ignored.add((logname, countryiso3, name))
            return None
        if not pcode:
            for map_name in name_to_pcode:
                if normalised_name in map_name:
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
                if alt_normalised_name in map_name:
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

            def al_transform_1(name):
                prefix = name[:3]
                if prefix == "al ":
                    return f"ad {name[3:]}"
                elif prefix == "ad ":
                    return f"al {name[3:]}"
                else:
                    return None

            def al_transform_2(name):
                prefix = name[:3]
                if prefix == "al " or prefix == "ad ":
                    return name[3:]
                else:
                    return None

            matching_index = self.phonetics.match(
                map_names,
                normalised_name,
                alternative_name=alt_normalised_name,
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

    def get_name_mapped_pcode(
        self, countryiso3: str, name: str, parent: str | None
    ) -> str | None:
        """Get pcode from admin name mappings which is a dictionary of mappings
        from name to pcode. These can be global or they can be restricted by
        country or parent (if the AdminLevel object has been set up with
        parents). Keys take the form "MAPPING", "AFG|MAPPING" or
        "AF01|MAPPING".

        Args:
            countryiso3: ISO3 country code
            name: Name to match
            parent: Parent admin code

        Returns:
            P code match from admin name mappings or None if no match
        """
        if parent:
            pcode = self.admin_name_mappings.get(f"{parent}|{name}")
            if pcode is None:
                pcode = self.admin_name_mappings.get(f"{countryiso3}|{name}")
        else:
            pcode = self.admin_name_mappings.get(f"{countryiso3}|{name}")
        if pcode is None:
            pcode = self.admin_name_mappings.get(name)
        return pcode

    def get_pcode(
        self,
        countryiso3: str,
        name: str,
        fuzzy_match: bool = True,
        fuzzy_length: int = 4,
        **kwargs: Any,
    ) -> tuple[str | None, bool]:
        """Get pcode for a given name

        Args:
            countryiso3: ISO3 country code
            name: Name to match
            fuzzy_match: Whether to try fuzzy matching. Defaults to True.
            fuzzy_length: Minimum length for fuzzy matching. Defaults to 4.
            **kwargs: See below
            parent (str): Parent admin code
            logname (str): Log using this identifying name. Defaults to not logging.

        Returns:
            (Matched P code or None if no match, True if exact match or False if not)
        """
        if self.use_parent:
            parent = kwargs.get("parent")
        else:
            parent = None
        pcode = self.get_name_mapped_pcode(countryiso3, name, parent)
        if pcode and self.pcode_to_iso3[pcode] == countryiso3:
            if parent:
                if self.pcode_to_parent[pcode] == parent:
                    return pcode, True
            else:
                return pcode, True
        if self.looks_like_pcode(name):
            pcode = name.upper()
            if pcode in self.pcodes:  # name is a p-code
                return name, True
            # name looks like a p-code, but doesn't match p-codes
            # so try adjusting p-code length
            pcode = self.convert_admin_pcode_length(countryiso3, pcode, **kwargs)
            return pcode, True
        else:
            normalised_name = normalise(name)
            if parent:
                name_parent_to_pcode = self.name_parent_to_pcode.get(countryiso3)
                if name_parent_to_pcode:
                    name_to_pcode = name_parent_to_pcode.get(parent)
                    if name_to_pcode is not None:
                        pcode = name_to_pcode.get(normalised_name)
                        if pcode:
                            return pcode, True
            else:
                name_to_pcode = self.name_to_pcode.get(countryiso3)
                if name_to_pcode is not None:
                    pcode = name_to_pcode.get(normalised_name)
                    if pcode:
                        return pcode, True
            if not fuzzy_match or len(normalised_name) < fuzzy_length:
                return None, True
            pcode = self.fuzzy_pcode(countryiso3, name, normalised_name, **kwargs)
            return pcode, False

    def output_matches(self) -> list[str]:
        """Output log of matches

        Returns:
            List of matches
        """
        output = []
        for match in sorted(self.matches):
            line = f"{match[0]} - {match[1]}: Matching ({match[4]}) {match[2]} to {match[3]} on map"
            logger.info(line)
            output.append(line)
        return output

    def output_ignored(self) -> list[str]:
        """Output log of ignored

        Returns:
            List of ignored
        """
        output = []
        for ignored in sorted(self.ignored):
            if len(ignored) == 2:
                line = f"{ignored[0]} - Ignored {ignored[1]}!"
            else:
                line = f"{ignored[0]} - {ignored[1]}: Ignored {ignored[2]}!"
            logger.info(line)
            output.append(line)
        return output

    def output_errors(self) -> list[str]:
        """Output log of errors

        Returns:
            List of errors
        """
        output = []
        for error in sorted(self.errors):
            if len(error) == 2:
                line = f"{error[0]} - Could not find {error[1]} in map names!"
            else:
                line = (
                    f"{error[0]} - {error[1]}: Could not find {error[2]} in map names!"
                )
            logger.error(line)
            output.append(line)
        return output

    def output_admin_name_mappings(self) -> list[str]:
        """Output log of name mappings

        Returns:
            List of mappings
        """
        output = []
        for name, pcode in self.admin_name_mappings.items():
            line = f"{name}: {self.pcode_to_name[pcode]} ({pcode})"
            logger.info(line)
            output.append(line)
        return output

    def output_admin_name_replacements(self) -> list[str]:
        """Output log of name replacements

        Returns:
            List of name replacements
        """
        output = []
        for name, replacement in self.admin_name_replacements.items():
            line = f"{name}: {replacement}"
            logger.info(line)
            output.append(line)
        return output
