# -*- coding: utf-8 -*-
import logging
from typing import Dict, Optional, Tuple, List

from hdx.location import clean_name, get_phonetics
from hdx.location.country import Country
from hdx.utilities.text import multiple_replace
from unidecode import unidecode

logger = logging.getLogger(__name__)


class AdminOne(object):
    """AdminOne class which takes in pcodes and then maps names to those pcodes with fuzzy matching if necessary. The
    input configuration dictionary, admin_config, requires key admin1_info which is a list with values of the form:
    ::
        {'iso3': 'AFG', 'pcode': 'AF01', 'name': 'Kabul'}

    Various other keys are optional:
    countries_fuzzy_try are countries (iso3 codes) for which to try fuzzy matching. Default is all countries.
    admin1_name_mappings is a dictionary of mappings from name to pcode (for where fuzzy matching fails)
    admin1_name_replacements is a dictionary of textual replacements to try when fuzzy matching
    admin1_fuzzy_dont is a list of names for which fuzzy matching should not be tried

    Args:
        admin_config (Dict): Configuration dictionary
        phonetics (Phonetics): Phonetics object to use. Defaults to None (new instance).
    """

    _admininfo = None
    pcodes = list()
    pcode_lengths = dict()
    name_to_pcode = dict()
    pcode_to_name = dict()
    pcode_to_iso3 = dict()

    def __init__(self, admin_config):
        # type: (Dict, object) -> None
        admin_info1 = admin_config['admin1_info']
        self.countries_fuzzy_try = admin_config.get('countries_fuzzy_try')
        self.admin1_name_mappings = admin_config.get('admin1_name_mappings', dict())
        self.admin1_name_replacements = admin_config.get('admin1_name_replacements', dict())
        self.admin1_fuzzy_dont = admin_config.get('admin1_fuzzy_dont', list())
        for row in admin_info1:
            countryiso3 = row['iso3']
            pcode = row.get('pcode')
            self.pcodes.append(pcode)
            self.pcode_lengths[countryiso3] = len(pcode)
            adm1_name = row['name']
            self.pcode_to_name[pcode] = adm1_name
            name_to_pcode = self.name_to_pcode.get(countryiso3, dict())
            name_to_pcode[unidecode(adm1_name).lower()] = pcode
            self.name_to_pcode[countryiso3] = name_to_pcode
            self.pcode_to_iso3[pcode] = countryiso3
        self.init_matches_errors()
        self.phonetics = get_phonetics()

    def init_matches_errors(self):
        # type: () -> None
        """Initialise storage of fuzzy matches, ignored and errors for logging purposes

        Returns:
            None
        """

        self.matches = set()
        self.ignored = set()
        self.errors = set()

    def convert_pcode_length(self, countryiso3, pcode, scrapername=None):
        # type: (str, str, Optional[str]) ->  Optional[str]
        """Standardise pcode length by country and match to an internal pcode

        Args:
            countryiso3 (str): Iso3 country code
            pcode (str): P code for admin one
            scrapername (Optional[str]): Name of scraper for logging purposes. Defaults to None (don't log).

        Returns:
            Optional[str]: Matched P code or None if no match
        """
        if pcode in self.pcodes:
            return pcode
        pcode_length = len(pcode)
        country_pcodelength = self.pcode_lengths.get(countryiso3)
        if not country_pcodelength:
            return None
        if pcode_length == country_pcodelength or pcode_length < 4 or pcode_length > 6:
            return None
        if country_pcodelength == 4:
            pcode = '%s%s' % (Country.get_iso2_from_iso3(pcode[:3]), pcode[-2:])
        elif country_pcodelength == 5:
            if pcode_length == 4:
                pcode = '%s0%s' % (pcode[:2], pcode[-2:])
            else:
                pcode = '%s%s' % (Country.get_iso2_from_iso3(pcode[:3]), pcode[-3:])
        elif country_pcodelength == 6:
            if pcode_length == 4:
                pcode = '%s0%s' % (Country.get_iso3_from_iso2(pcode[:2]), pcode[-2:])
            else:
                pcode = '%s%s' % (Country.get_iso3_from_iso2(pcode[:2]), pcode[-3:])
        else:
            pcode = None
        if pcode in self.pcodes:
            if scrapername:
                self.matches.add((scrapername, countryiso3, pcode, self.pcode_to_name[pcode], 'pcode length conversion'))
            return pcode
        return None

    def fuzzy_pcode(self, countryiso3, name, scrapername=None):
        # type: (str, str, Optional[str]) ->  Optional[str]
        """Fuzzy match name to pcode

        Args:
            countryiso3 (str): Iso3 country code
            name (str): Name to match
            scrapername (Optional[str]): Name of scraper for logging purposes. Defaults to None (don't log).

        Returns:
            Optional[str]: Matched P code or None if no match
        """
        if self.countries_fuzzy_try is not None and countryiso3 not in self.countries_fuzzy_try:
            self.ignored.add((scrapername, countryiso3))
            return None
        name_to_pcode = self.name_to_pcode.get(countryiso3)
        if not name_to_pcode:
            self.errors.add((scrapername, countryiso3))
            return None
        if name.lower() in self.admin1_fuzzy_dont:
            self.ignored.add((scrapername, countryiso3, name))
            return None
        adm1_name_lookup = clean_name(name)
        adm1_name_lookup2 = multiple_replace(adm1_name_lookup, self.admin1_name_replacements)
        pcode = name_to_pcode.get(adm1_name_lookup, name_to_pcode.get(adm1_name_lookup2))
        if not pcode:
            for map_name in name_to_pcode:
                if adm1_name_lookup in map_name:
                    pcode = name_to_pcode[map_name]
                    self.matches.add((scrapername, countryiso3, name, self.pcode_to_name[pcode], 'substring'))
                    break
            for map_name in name_to_pcode:
                if adm1_name_lookup2 in map_name:
                    pcode = name_to_pcode[map_name]
                    self.matches.add((scrapername, countryiso3, name, self.pcode_to_name[pcode], 'substring'))
                    break
        if not pcode:
            map_names = list(name_to_pcode.keys())
            lower_mapnames = [x.lower() for x in map_names]

            def al_transform_1(name):
                if name[:3] == 'al ':
                    return 'ad %s' % name[3:]
                else:
                    return None

            def al_transform_2(name):
                if name[:3] == 'al ':
                    return name[3:]
                else:
                    return None

            matching_index = self.phonetics.match(lower_mapnames, adm1_name_lookup, alternative_name=adm1_name_lookup2,
                                                  transform_possible_names=[al_transform_1, al_transform_2])

            if matching_index is None:
                self.errors.add((scrapername, countryiso3, name))
                return None

            map_name = map_names[matching_index]
            pcode = name_to_pcode[map_name]
            self.matches.add((scrapername, countryiso3, name, self.pcode_to_name[pcode], 'fuzzy'))
        return pcode

    def get_pcode(self, countryiso3, name, scrapername=None):
        # type: (str, str, Optional[str]) ->  Tuple[Optional[str], bool]
        """Get pcode for a given name

        Args:
            countryiso3 (str): Iso3 country code
            name (str): Name to match
            scrapername (Optional[str]): Name of scraper for logging purposes. Defaults to None (don't log).

        Returns:
            Tuple[Optional[str], bool]: (Matched P code or None if no match, True if exact match or False if not)
        """
        pcode = self.admin1_name_mappings.get(name)
        if pcode and self.pcode_to_iso3[pcode] == countryiso3:
            return pcode, True
        name_to_pcode = self.name_to_pcode.get(countryiso3)
        if name_to_pcode is not None:
            pcode = name_to_pcode.get(name.lower())
            if pcode:
                return pcode, True
        pcode = self.convert_pcode_length(countryiso3, name, scrapername)
        if pcode:
            adm = pcode
            exact = True
        else:
            adm = self.fuzzy_pcode(countryiso3, name, scrapername)
            exact = False
        return adm, exact

    def output_matches(self):
        # type: () ->  List[str]
        """Output log of matches

        Returns:
            List[str]: List of matches
        """
        output = list()
        for match in sorted(self.matches):
            line = '%s - %s: Matching (%s) %s to %s on map' % (match[0], match[1], match[4], match[2], match[3])
            logger.info(line)
            output.append(line)
        return output

    def output_ignored(self):
        # type: () ->  List[str]
        """Output log of ignored

        Returns:
            List[str]: List of ignored
        """
        output = list()
        for ignored in sorted(self.ignored):
            if len(ignored) == 2:
                line = '%s - Ignored %s!' % (ignored[0], ignored[1])
            else:
                line = '%s - %s: Ignored %s!' % (ignored[0], ignored[1], ignored[2])
            logger.info(line)
            output.append(line)
        return output

    def output_errors(self):
        # type: () ->  List[str]
        """Output log of errors

        Returns:
            List[str]: List of errors
        """
        output = list()
        for error in sorted(self.errors):
            if len(error) == 2:
                line = '%s - Could not find %s in map names!' % (error[0], error[1])
            else:
                line = '%s - %s: Could not find %s in map names!' % (error[0], error[1], error[2])
            logger.error(line)
            output.append(line)
        return output
