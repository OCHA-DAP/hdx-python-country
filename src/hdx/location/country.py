# -*- coding: utf-8 -*-
"""Country location"""
import copy
import logging
import re
from typing import List, Tuple, Optional, TypeVar, Dict, Any, Union

from bs4 import BeautifulSoup
from hdx.utilities.downloader import Download, DownloadError
from hdx.utilities.html import extract_table
from hdx.utilities.loader import load_json, load_file_to_str
from hdx.utilities.path import script_dir_plus_file
from hdx.utilities.text import get_words_in_sentence

ExceptionUpperBound = TypeVar('T', bound='Exception')


logger = logging.getLogger(__name__)


class CountryError(Exception):
    pass


class Country(object):
    """Location class with various methods to help with countries and regions. Uses UNStats M49 webpage which
    supplies data in form:
    ::
              <table id = "downloadTableEN" class="compact" cellspacing="0" width="100%" >
        <thead>
          <tr>
            <td>Global Code</td>
            <td>Global Name</td>
            <td>Region Code</td>
            <td>Region Name</td>
            <td>Sub-region Code</td>
            <td>Sub-region Name</td>
            <td>Intermediate Region Code</td>
            <td>Intermediate Region Name</td>
            <td>Country or Area</td>
            <td>M49 Code</td>
            <td>ISO-alpha3 Code</td>
            <td>Least Developed Countries (LDC)</td>
            <td>Land Locked Developing Countries (LLDC)</td>
            <td>Small Island Developing States (SIDS)</td>
            <td>Developed / Developing Countries</td>
          </tr>
        </thead>
        <tbody>
                              <tr>
                                <td>001</td>
                                <td>World</td>
                                <td>002</td>
                                <td>Africa</td>
                                <td>015</td>
                                <td>Northern Africa</td>
                                <td></td>
                                <td></td>
                                <td>Algeria</td>
                                <td>012</td>
                                <td>DZA</td>
                                <td>                                </td>
                                <td>                                </td>
                                <td>                                </td>
                                <td>                                  <code>Developing</code>
                                </td>
                              </tr>
                              ...


    and World Bank API which supplies data in form:
    ::
        {'id': 'AFG', 'iso2Code': 'AF', 'name': 'Afghanistan',
        'latitude': '34.5228', 'longitude': '69.1761',
        'region': {'value': 'South Asia', 'id': 'SAS'},
        'adminregion': {'value': 'South Asia', 'id': 'SAS'},
        'capitalCity': 'Kabul',
        'lendingType': {'value': 'IDA', 'id': 'IDX'},
        'incomeLevel': {'value': 'Low income', 'id': 'LIC'}}

    """

    abbreviations = {'DEM.': 'DEMOCRATIC', 'FMR.': 'FORMER', 'PROV.': 'PROVINCE', 'REP.': 'REPUBLIC', 'ST.': 'SAINT',
                     'UTD.': 'UNITED', 'U.': 'UNITED', 'N.': 'NORTH', 'E.': 'EAST', 'W.': 'WEST', 'K.': 'KINGDOM'}
    major_differentiators = ['DEMOCRATIC', 'NORTH', 'SOUTH', 'EAST', 'WEST', 'STATES']
    multiple_abbreviations = {'FED.': ['FEDERATION', 'FEDERAL', 'FEDERATED'],
                              'ISL.': ['ISLAND', 'ISLANDS'],
                              'S.': ['SOUTH', 'STATES'],
                              'TERR.': ['TERRITORY', 'TERRITORIES']}
    simplifications = ['THE', 'OF', 'ISLAMIC', 'STATES', 'BOLIVARIAN', 'PLURINATIONAL', "PEOPLE'S",
                       'DUTCH PART', 'FRENCH PART', 'MALVINAS', 'YUGOSLAV', 'KINGDOM', 'PROTECTORATE']
    _countriesdata = None
    _wburl_int = 'http://api.worldbank.org/countries?format=json&per_page=10000'
    _wburl = _wburl_int
    _unstatsurl_int = 'https://unstats.un.org/unsd/methodology/m49/overview/'
    _unstatsurl = _unstatsurl_int
    _unstatstablename_int = 'downloadTableEN'
    _unstatstablename = _unstatstablename_int
    _globalname = None

    @classmethod
    def _add_countriesdata(cls, iso3, country, regioncodefromname=False):
        # type: (str, Dict, bool) -> None
        """
        Set up countries data from data in form provided by UNStats and World Bank

        Args:
            iso3 (str): ISO3 code for country
            country (Dict): Country information
            regioncodefromname (bool): Whether to read region code from existing mapping

        Returns:
            None
        """
        countryname = country['Country or Area']
        cls._countriesdata['countrynames2iso3'][countryname.upper()] = iso3
        m49 = country['M49 Code']
        if m49:
            m49 = int(m49)
            country['M49 Code'] = m49
            cls._countriesdata['m49iso3'][m49] = iso3
            # different types so keys won't clash
            cls._countriesdata['m49iso3'][iso3] = m49
        ison = country['ISO-numeric Code']
        if ison:
            ison = int(ison)
            country['ISO-numeric Code'] = ison
            cls._countriesdata['isoniso3'][ison] = iso3
            # different types so keys won't clash
            cls._countriesdata['isoniso3'][iso3] = ison
        globalname = country.get('Global Name', Country._globalname)
        Country._globalname = globalname
        country['Global Name'] = globalname
        regionname = country['Region Name']
        sub_regionname = country['Sub-region Name']
        intermediate_regionname = country['Intermediate Region Name']
        if regioncodefromname:
            globalid = cls._countriesdata['regionnames2codes'].get(globalname.upper())
            country['Global Code'] = globalid
            if regionname:
                regionid = cls._countriesdata['regionnames2codes'].get(regionname.upper())
                country['Region Code'] = regionid
            if sub_regionname:
                sub_regionid = cls._countriesdata['regionnames2codes'].get(sub_regionname.upper())
                country['Sub-region Code'] = sub_regionid
            if intermediate_regionname:
                intermediate_regionid = cls._countriesdata['regionnames2codes'].get(intermediate_regionname.upper())
                country['Intermediate Region Code'] = intermediate_regionid
        else:
            globalid = country['Global Code']
            if globalid:
                globalid = int(globalid)
                country['Global Code'] = globalid
            regionid = country['Region Code']
            if regionid:
                regionid = int(regionid)
                country['Region Code'] = regionid
            sub_regionid = country['Sub-region Code']
            if sub_regionid:
                sub_regionid = int(sub_regionid)
                country['Sub-region Code'] = sub_regionid
            intermediate_regionid = country['Intermediate Region Code']
            if intermediate_regionid:
                intermediate_regionid = int(intermediate_regionid)
                country['Intermediate Region Code'] = intermediate_regionid

        # region, subregion and intermediate region codes do not clash so only need one dict
        def add_country_to_set(colname, idval, iso3):
            value = cls._countriesdata[colname].get(idval)
            if value is None:
                value = set()
                cls._countriesdata['regioncodes2countries'][idval] = value
            value.add(iso3)

        if globalname:
            add_country_to_set('regioncodes2countries', globalid, iso3)
            cls._countriesdata['regioncodes2names'][globalid] = globalname
            cls._countriesdata['regionnames2codes'][globalname.upper()] = globalid
        if regionname:
            add_country_to_set('regioncodes2countries', regionid, iso3)
            cls._countriesdata['regioncodes2names'][regionid] = regionname
            cls._countriesdata['regionnames2codes'][regionname.upper()] = regionid
        if sub_regionname:
            add_country_to_set('regioncodes2countries', sub_regionid, iso3)
            cls._countriesdata['regioncodes2names'][sub_regionid] = sub_regionname
            cls._countriesdata['regionnames2codes'][sub_regionname.upper()] = sub_regionid
        if intermediate_regionname:
            add_country_to_set('regioncodes2countries', intermediate_regionid, iso3)
            cls._countriesdata['regioncodes2names'][intermediate_regionid] = intermediate_regionname
            cls._countriesdata['regionnames2codes'][intermediate_regionname.upper()] = \
                intermediate_regionid

    @classmethod
    def set_countriesdata(cls, json, html, fallbacks, aliases):
        # type: (Any, str, Dict, Dict) -> None
        """
        Set up countries data from data in form provided by UNStats and World Bank

        Args:
            json (Any): Countries data in JSON format provided by World Bank
            html (str): Countries data in HTML format provided by UNStats
            fallbacks (Dict): Fallback internal table
            aliases (Dict): Country regex

        Returns:
            None
        """
        tabletag = BeautifulSoup(html, 'html.parser').find(id=cls._unstatstablename)
        if tabletag is None:
            raise CountryError('Could not find UNStats HTML table %s!' % cls._unstatstablename)
        unstatstable = extract_table(tabletag)
        if len(unstatstable) == 0:
            raise CountryError('Could not read any rows from UNStats HTML table %s!' % cls._unstatstablename)
        cls._countriesdata = dict()
        cls._countriesdata['countries'] = dict()
        cls._countriesdata['iso2iso3'] = dict()
        cls._countriesdata['m49iso3'] = dict()
        cls._countriesdata['isoniso3'] = dict()
        cls._countriesdata['countrynames2iso3'] = dict()
        cls._countriesdata['regioncodes2countries'] = dict()
        cls._countriesdata['regioncodes2names'] = dict()
        cls._countriesdata['regionnames2codes'] = dict()
        cls._countriesdata['aliases'] = dict()

        for country in unstatstable:
            iso3 = country['ISO-alpha3 Code'].upper()
            if not iso3:
                continue
            country['ISO-numeric Code'] = country['M49 Code']
            cls._add_countriesdata(iso3, country)
            for key in country:
                if not country[key]:
                    country[key] = None
            cls._countriesdata['countries'][iso3] = country

        def fix_fallback(fallbackcountry):
            for key in fallbackcountry:
                val = fallbackcountry[key]
                if val:
                    try:
                        val = int(fallbackcountry[key])
                        fallbackcountry[key] = val
                    except ValueError:
                        pass
                else:
                    fallbackcountry[key] = None

        for wbcountry in json[1]:
            if wbcountry['region']['value'] != 'Aggregates':
                countryname = wbcountry['name']
                iso2 = wbcountry['iso2Code'].upper()
                iso3 = wbcountry['id'].upper()
                capital = wbcountry['capitalCity']
                if not capital:
                    capital = None
                # different no. of chars so keys won't clash
                cls._countriesdata['iso2iso3'][iso2] = iso3
                cls._countriesdata['iso2iso3'][iso3] = iso2
                country = cls._countriesdata['countries'].get(iso3)
                if country:
                    country['ISO-alpha2 Code'] = iso2
                    country['Capital City'] = capital
                else:
                    fallbackcountry = fallbacks.get(iso3)
                    if not fallbackcountry or not fallbackcountry['obsolete']:
                        cls._countriesdata['countries'][iso3] = {'Country or Area': countryname,
                                                                 'ISO-alpha2 Code': iso2,
                                                                 'ISO-alpha3 Code': iso3,
                                                                 'Capital City': capital}
                        cls._countriesdata['countrynames2iso3'][countryname.upper()] = iso3
                    if fallbackcountry and not fallbackcountry['obsolete']:
                        cls._add_countriesdata(iso3, fallbackcountry, regioncodefromname=True)
                        fix_fallback(fallbackcountry)
                        cls._countriesdata['countries'][iso3].update(fallbackcountry)
                        del cls._countriesdata['countries'][iso3]['obsolete']

        for iso3 in fallbacks:
            country = cls._countriesdata['countries'].get(iso3)
            fallbackcountry = fallbacks[iso3]
            if not country and not fallbackcountry['obsolete']:
                fix_fallback(fallbackcountry)
                cls._countriesdata['countries'][iso3] = fallbackcountry
                del cls._countriesdata['countries'][iso3]['obsolete']
                cls._add_countriesdata(iso3, fallbackcountry, regioncodefromname=True)

        cls._countriesdata['aliases'] = aliases

        def sort_list(colname):
            for idval in cls._countriesdata[colname]:
                cls._countriesdata[colname][idval] = \
                    sorted(list(cls._countriesdata[colname][idval]))

        sort_list('regioncodes2countries')

    @classmethod
    def countriesdata(cls, use_live=True):
        # type: (bool) -> List[Dict[Dict]]
        """
        Read countries data from UNStats M49 website and World Bank API (falling back to file)

        Args:
            use_live (bool): Try to get use latest data from web rather than file in package. Defaults to True.

        Returns:
            List[Dict[Dict]]: Countries dictionaries
        """
        if cls._countriesdata is None:
            with Download() as downloader:
                json = None
                html = None
                if use_live:
                    try:
                        response = downloader.download(cls._wburl)
                        json = response.json()
                    except DownloadError:
                        logger.exception('Download from World Bank API failed! Falling back to stored file.')
                    try:
                        response = downloader.download(cls._unstatsurl)
                        html = response.text
                    except DownloadError:
                        logger.exception('Scrape from UNStats website failed! Falling back to stored file.')
                if json is None:
                    json = load_json(script_dir_plus_file('worldbank.json', Country))
                if html is None:
                    html = load_file_to_str(script_dir_plus_file('unstats.html', Country))
                fallbacks = dict()
                aliases = dict()
                for country in downloader.get_tabular_rows(script_dir_plus_file('country_data.tsv', Country),
                                                           format='csv',
                                                           delimiter='\t', dict_rows=True, headers=1):
                    iso3 = country['ISO3']
                    aliases[iso3] = re.compile(country['regex'], re.IGNORECASE)
                    fallbacks[iso3] = {'Country or Area': country['name_official'],
                                       'ISO-alpha2 Code': country['ISO2'],
                                       'M49 Code': country['UNcode'],
                                       'ISO-numeric Code': country['ISOnumeric'],
                                       'Region Name': country['continent'],
                                       'Sub-region Name': country['UNregion'],
                                       'Intermediate Region Code': '',
                                       'Intermediate Region Name': '',
                                       'obsolete': country['obsolete']}
                cls.set_countriesdata(json, html, fallbacks, aliases)
        return cls._countriesdata

    @classmethod
    def set_worldbank_url(cls, url=None):
        # type: (str) -> None
        """
        Set World Bank url from which to retrieve countries data

        Args:
            url (str): World Bank url from which to retrieve countries data. Defaults to internal value.

        Returns:
            None
        """
        if url is None:
            url = cls._wburl_int
        cls._wburl = url

    @classmethod
    def set_unstats_url_tablename(cls, url=None, tablename=None):
        # type: (str, str) -> None
        """
        Set UN Stats url and HTMl table name from which to retrieve countries data

        Args:
            url (str): UN Stats url from which to retrieve countries data. Defaults to internal value.
            tablename (str): UN Stats HTML table name from which to retrieve countries data. Defaults to internal value.

        Returns:
            None
        """
        if url is None:
            url = cls._unstatsurl_int
        cls._unstatsurl = url
        if tablename is None:
            tablename = cls._unstatstablename_int
        cls._unstatstablename = tablename

    @classmethod
    def get_country_info_from_iso3(cls, iso3, use_live=True, exception=None):
        # type: (str, bool, Optional[ExceptionUpperBound]) -> Optional[Dict[str]]
        """Get country information from ISO3 code

        Args:
            iso3 (str): ISO3 code for which to get country information
            use_live (bool): Try to get use latest data from web rather than file in package. Defaults to True.
            exception (Optional[ExceptionUpperBound]): An exception to raise if country not found. Defaults to None.

        Returns:
            Optional[Dict[str]]: country information
        """
        countriesdata = cls.countriesdata(use_live=use_live)
        country = countriesdata['countries'].get(iso3.upper())
        if country is not None:
            return country

        if exception is not None:
            raise exception
        return None

    @classmethod
    def get_country_name_from_iso3(cls, iso3, use_live=True, exception=None):
        # type: (str, bool, Optional[ExceptionUpperBound]) -> Optional[str]
        """Get country name from ISO3 code

        Args:
            iso3 (str): ISO3 code for which to get country name
            use_live (bool): Try to get use latest data from web rather than file in package. Defaults to True.
            exception (Optional[ExceptionUpperBound]): An exception to raise if country not found. Defaults to None.

        Returns:
            Optional[str]: Country name
        """
        countryinfo = cls.get_country_info_from_iso3(iso3, use_live=use_live, exception=exception)
        if countryinfo is not None:
            return countryinfo['Country or Area']
        return None

    @classmethod
    def get_iso2_from_iso3(cls, iso3, use_live=True, exception=None):
        # type: (str, bool, Optional[ExceptionUpperBound]) -> Optional[str]
        """Get ISO2 from ISO3 code

        Args:
            iso3 (str): ISO3 code for which to get ISO2 code
            use_live (bool): Try to get use latest data from web rather than file in package. Defaults to True.
            exception (Optional[ExceptionUpperBound]): An exception to raise if country not found. Defaults to None.

        Returns:
            Optional[str]: ISO2 code
        """
        countriesdata = cls.countriesdata(use_live=use_live)
        iso2 = countriesdata['iso2iso3'].get(iso3.upper())
        if iso2 is not None:
            return iso2

        if exception is not None:
            raise exception
        return None

    @classmethod
    def get_iso3_from_iso2(cls, iso2, use_live=True, exception=None):
        # type: (str, bool, Optional[ExceptionUpperBound]) -> Optional[str]
        """Get ISO3 from ISO2 code

        Args:
            iso2 (str): ISO2 code for which to get ISO3 code
            use_live (bool): Try to get use latest data from web rather than file in package. Defaults to True.
            exception (Optional[ExceptionUpperBound]): An exception to raise if country not found. Defaults to None.

        Returns:
            Optional[str]: ISO3 code
        """
        countriesdata = cls.countriesdata(use_live=use_live)
        iso3 = countriesdata['iso2iso3'].get(iso2.upper())
        if iso3 is not None:
            return iso3

        if exception is not None:
            raise exception
        return None

    @classmethod
    def get_country_info_from_iso2(cls, iso2, use_live=True, exception=None):
        # type: (str, bool, Optional[ExceptionUpperBound]) -> Optional[Dict[str]]
        """Get country name from ISO2 code

        Args:
            iso2 (str): ISO2 code for which to get country information
            use_live (bool): Try to get use latest data from web rather than file in package. Defaults to True.
            exception (Optional[ExceptionUpperBound]): An exception to raise if country not found. Defaults to None.

        Returns:
            Optional[Dict[str]]: Country information
        """
        iso3 = cls.get_iso3_from_iso2(iso2, use_live=use_live, exception=exception)
        if iso3 is not None:
            return cls.get_country_info_from_iso3(iso3, use_live=use_live, exception=exception)
        return None

    @classmethod
    def get_country_name_from_iso2(cls, iso2, use_live=True, exception=None):
        # type: (str, bool, Optional[ExceptionUpperBound]) -> Optional[str]
        """Get country name from ISO2 code

        Args:
            iso2 (str): ISO2 code for which to get country name
            use_live (bool): Try to get use latest data from web rather than file in package. Defaults to True.
            exception (Optional[ExceptionUpperBound]): An exception to raise if country not found. Defaults to None.

        Returns:
            Optional[str]: Country name
        """
        iso3 = cls.get_iso3_from_iso2(iso2, use_live=use_live, exception=exception)
        if iso3 is not None:
            return cls.get_country_name_from_iso3(iso3, exception=exception)
        return None

    @classmethod
    def get_m49_from_iso3(cls, iso3, use_live=True, exception=None):
        # type: (str, bool, Optional[ExceptionUpperBound]) -> Optional[int]
        """Get M49 from ISO3 code

        Args:
            iso3 (str): ISO3 code for which to get M49 code
            use_live (bool): Try to get use latest data from web rather than file in package. Defaults to True.
            exception (Optional[ExceptionUpperBound]): An exception to raise if country not found. Defaults to None.

        Returns:
            Optional[int]: M49 code
        """
        countriesdata = cls.countriesdata(use_live=use_live)
        m49 = countriesdata['m49iso3'].get(iso3)
        if m49 is not None:
            return m49

        if exception is not None:
            raise exception
        return None

    @classmethod
    def get_iso3_from_m49(cls, m49, use_live=True, exception=None):
        # type: (int, bool, Optional[ExceptionUpperBound]) -> Optional[str]
        """Get ISO3 from M49 code

        Args:
            m49 (int): M49 numeric code for which to get ISO3 code
            use_live (bool): Try to get use latest data from web rather than file in package. Defaults to True.
            exception (Optional[ExceptionUpperBound]): An exception to raise if country not found. Defaults to None.

        Returns:
            Optional[str]: ISO3 code
        """
        countriesdata = cls.countriesdata(use_live=use_live)
        iso3 = countriesdata['m49iso3'].get(m49)
        if iso3 is not None:
            return iso3

        if exception is not None:
            raise exception
        return None

    @classmethod
    def get_country_info_from_m49(cls, m49, use_live=True, exception=None):
        # type: (int, bool, Optional[ExceptionUpperBound]) -> Optional[Dict[str]]
        """Get country name from M49 code

        Args:
            m49 (int): M49 numeric code for which to get country information
            use_live (bool): Try to get use latest data from web rather than file in package. Defaults to True.
            exception (Optional[ExceptionUpperBound]): An exception to raise if country not found. Defaults to None.

        Returns:
            Optional[Dict[str]]: Country information
        """
        iso3 = cls.get_iso3_from_m49(m49, use_live=use_live, exception=exception)
        if iso3 is not None:
            return cls.get_country_info_from_iso3(iso3, exception=exception)
        return None

    @classmethod
    def get_country_name_from_m49(cls, m49, use_live=True, exception=None):
        # type: (int, bool, Optional[ExceptionUpperBound]) -> Optional[str]
        """Get country name from M49 code

        Args:
            m49 (int): M49 numeric code for which to get country name
            use_live (bool): Try to get use latest data from web rather than file in package. Defaults to True.
            exception (Optional[ExceptionUpperBound]): An exception to raise if country not found. Defaults to None.

        Returns:
            Optional[str]: Country name
        """
        iso3 = cls.get_iso3_from_m49(m49, use_live=use_live, exception=exception)
        if iso3 is not None:
            return cls.get_country_name_from_iso3(iso3, exception=exception)
        return None

    @classmethod
    def get_ison_from_iso3(cls, iso3, use_live=True, exception=None):
        # type: (str, bool, Optional[ExceptionUpperBound]) -> Optional[int]
        """Get ISO numeric code from ISO3 code

        Args:
            iso3 (str): ISO3 code for which to get M49 code
            use_live (bool): Try to get use latest data from web rather than file in package. Defaults to True.
            exception (Optional[ExceptionUpperBound]): An exception to raise if country not found. Defaults to None.

        Returns:
            Optional[int]: ISO numeric code
        """
        countriesdata = cls.countriesdata(use_live=use_live)
        ison = countriesdata['isoniso3'].get(iso3)
        if ison is not None:
            return ison

        if exception is not None:
            raise exception
        return None

    @classmethod
    def get_iso3_from_ison(cls, ison, use_live=True, exception=None):
        # type: (int, bool, Optional[ExceptionUpperBound]) -> Optional[str]
        """Get ISO3 from ISO numeric code

        Args:
            ison (int): ISO numeric code for which to get ISO3 code
            use_live (bool): Try to get use latest data from web rather than file in package. Defaults to True.
            exception (Optional[ExceptionUpperBound]): An exception to raise if country not found. Defaults to None.

        Returns:
            Optional[str]: ISO3 code
        """
        countriesdata = cls.countriesdata(use_live=use_live)
        iso3 = countriesdata['isoniso3'].get(ison)
        if iso3 is not None:
            return iso3

        if exception is not None:
            raise exception
        return None

    @classmethod
    def get_country_info_from_ison(cls, ison, use_live=True, exception=None):
        # type: (int, bool, Optional[ExceptionUpperBound]) -> Optional[Dict[str]]
        """Get country name from M49 code

        Args:
            ison (int): ISO numeric code for which to get country information
            use_live (bool): Try to get use latest data from web rather than file in package. Defaults to True.
            exception (Optional[ExceptionUpperBound]): An exception to raise if country not found. Defaults to None.

        Returns:
            Optional[Dict[str]]: Country information
        """
        iso3 = cls.get_iso3_from_ison(ison, use_live=use_live, exception=exception)
        if iso3 is not None:
            return cls.get_country_info_from_iso3(iso3, exception=exception)
        return None

    @classmethod
    def get_country_name_from_ison(cls, ison, use_live=True, exception=None):
        # type: (int, bool, Optional[ExceptionUpperBound]) -> Optional[str]
        """Get country name from M49 code

        Args:
            ison (int): ISO numeric code for which to get country name
            use_live (bool): Try to get use latest data from web rather than file in package. Defaults to True.
            exception (Optional[ExceptionUpperBound]): An exception to raise if country not found. Defaults to None.

        Returns:
            Optional[str]: Country name
        """
        iso3 = cls.get_iso3_from_ison(ison, use_live=use_live, exception=exception)
        if iso3 is not None:
            return cls.get_country_name_from_iso3(iso3, exception=exception)
        return None

    @classmethod
    def expand_countryname_abbrevs(cls, country):
        # type: (str) -> List[str]
        """Expands abbreviation(s) in country name in various ways (eg. FED -> FEDERATED, FEDERAL etc.)

        Args:
            country (str): Country with abbreviation(s)to expand

        Returns:
            List[str]: Uppercase country name with abbreviation(s) expanded in various ways
        """
        def replace_ensure_space(word, replace, replacement):
            return word.replace(replace, '%s ' % replacement).replace('  ', ' ').strip()
        countryupper = country.upper()
        for abbreviation in cls.abbreviations:
            countryupper = replace_ensure_space(countryupper, abbreviation, cls.abbreviations[abbreviation])
        candidates = [countryupper]
        for abbreviation in cls.multiple_abbreviations:
            if abbreviation in countryupper:
                for expanded in cls.multiple_abbreviations[abbreviation]:
                    candidates.append(replace_ensure_space(countryupper, abbreviation, expanded))
        return candidates

    @classmethod
    def simplify_countryname(cls, country):
        # type: (str) -> (str, List[str])
        """Simplifies country name by removing descriptive text eg. DEMOCRATIC, REPUBLIC OF etc.

        Args:
            country (str): Country name to simplify

        Returns:
            Tuple[str, List[str]]: Uppercase simplified country name and list of removed words
        """
        countryupper = country.upper()
        words = get_words_in_sentence(countryupper)
        index = countryupper.find(',')
        if index != -1:
            countryupper = countryupper[:index]
        index = countryupper.find(':')
        if index != -1:
            countryupper = countryupper[:index]
        regex = re.compile('\(.+?\)')
        countryupper = regex.sub('', countryupper)
        remove = copy.deepcopy(cls.simplifications)
        for simplification1, simplification2 in cls.abbreviations.items():
            countryupper = countryupper.replace(simplification1, '')
            remove.append(simplification2)
        for simplification1, simplifications in cls.multiple_abbreviations.items():
            countryupper = countryupper.replace(simplification1, '')
            for simplification2 in simplifications:
                remove.append(simplification2)
        remove = '|'.join(remove)
        regex = re.compile(r'\b(' + remove + r')\b', flags=re.IGNORECASE)
        countryupper = regex.sub('', countryupper)
        countryupper = countryupper.strip()
        countryupper_words = get_words_in_sentence(countryupper)
        if len(countryupper_words) > 1:
            countryupper = countryupper_words[0]
        if countryupper:
            words.remove(countryupper)
        return countryupper, words

    @classmethod
    def get_iso3_country_code(cls, country, use_live=True, exception=None):
        # type: (str, bool, Optional[ExceptionUpperBound]) -> Optional[str]
        """Get ISO3 code for cls. Only exact matches or None are returned.

        Args:
            country (str): Country for which to get ISO3 code
            use_live (bool): Try to get use latest data from web rather than file in package. Defaults to True.
            exception (Optional[ExceptionUpperBound]): An exception to raise if country not found. Defaults to None.

        Returns:
            Optional[str]: ISO3 country code or None
        """
        countriesdata = cls.countriesdata(use_live=use_live)
        countryupper = country.upper()
        len_countryupper = len(countryupper)
        if len_countryupper == 3:
            if countryupper in countriesdata['countries']:
                return countryupper
        elif len_countryupper == 2:
            iso3 = countriesdata['iso2iso3'].get(countryupper)
            if iso3 is not None:
                return iso3

        iso3 = countriesdata['countrynames2iso3'].get(countryupper)
        if iso3 is not None:
            return iso3

        for candidate in cls.expand_countryname_abbrevs(countryupper):
            iso3 = countriesdata['countrynames2iso3'].get(candidate)
            if iso3 is not None:
                return iso3

        if exception is not None:
            raise exception
        return None

    @classmethod
    def get_iso3_country_code_fuzzy(cls, country, use_live=True, exception=None):
        # type: (str, bool, Optional[ExceptionUpperBound]) -> Tuple[[Optional[str], bool]]
        """Get ISO3 code for cls. A tuple is returned with the first value being the ISO3 code and the second
        showing if the match is exact or not.

        Args:
            country (str): Country for which to get ISO3 code
            use_live (bool): Try to get use latest data from web rather than file in package. Defaults to True.
            exception (Optional[ExceptionUpperBound]): An exception to raise if country not found. Defaults to None.

        Returns:
            Tuple[[Optional[str], bool]]: ISO3 code and if the match is exact or (None, False).
        """
        countriesdata = cls.countriesdata(use_live=use_live)
        iso3 = cls.get_iso3_country_code(country,
                                         use_live=use_live)  # don't put exception param here as we don't want it to throw

        if iso3 is not None:
            return iso3, True

        def remove_matching_from_list(wordlist, word_or_part):
            for word in wordlist:
                if word_or_part in word:
                    wordlist.remove(word)

        # fuzzy matching
        expanded_country_candidates = cls.expand_countryname_abbrevs(country)
        match_strength = 0
        matches = set()
        for countryname in sorted(countriesdata['countrynames2iso3']):
            for candidate in expanded_country_candidates:
                simplified_country, removed_words = cls.simplify_countryname(candidate)
                if simplified_country in countryname:
                    words = get_words_in_sentence(countryname)
                    new_match_strength = 0
                    if simplified_country:
                        remove_matching_from_list(words, simplified_country)
                        new_match_strength += 32
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
                    iso3 = countriesdata['countrynames2iso3'][countryname]
                    if new_match_strength > match_strength:
                        match_strength = new_match_strength
                        matches = set()
                    if new_match_strength == match_strength:
                        matches.add(iso3)

        if len(matches) == 1 and match_strength > 16:
            return matches.pop(), False

        # regex lookup
        for iso3, regex in countriesdata['aliases'].items():
            index = re.search(regex, country.upper())
            if index is not None:
                return iso3, False

        if exception is not None:
            raise exception
        return None, False

    @classmethod
    def get_countries_in_region(cls, region, use_live=True, exception=None):
        # type: (Union[int,str], bool, Optional[ExceptionUpperBound]) -> List[str]
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
            regioncode = countriesdata['regionnames2codes'].get(regionupper)

        if regioncode is not None:
            return countriesdata['regioncodes2countries'][regioncode]

        if exception is not None:
            raise exception
        return list()
