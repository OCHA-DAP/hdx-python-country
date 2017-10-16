# -*- coding: utf-8 -*-
"""Country location"""
import logging
from typing import List, Tuple, Optional, TypeVar, Dict

from hdx.utilities.downloader import Download, DownloadError
from hdx.utilities.loader import load_json
from hdx.utilities.path import script_dir_plus_file

ExceptionUpperBound = TypeVar('T', bound='Exception')


logger = logging.getLogger(__name__)


class Country(object):
    """Location class with various methods to help with countries and regions. Uses World Bank API which supplies data
    in form:
    ::
        {'id': 'AFG', 'iso2Code': 'AF', 'name': 'Afghanistan',
        'latitude': '34.5228', 'longitude': '69.1761',
        'region': {'value': 'South Asia', 'id': 'SAS'},
        'adminregion': {'value': 'South Asia', 'id': 'SAS'},
        'capitalCity': 'Kabul',
        'lendingType': {'value': 'IDA', 'id': 'IDX'},
        'incomeLevel': {'value': 'Low income', 'id': 'LIC'}}

    Valid regions are:
    ::
        {'EAS': 'East Asia & Pacific', 'SAS': 'South Asia',
        'MEA': 'Middle East & North Africa', 'ECS': 'Europe & Central Asia',
        'LCN': 'Latin America & Caribbean ', 'NAC': 'North America',
        'SSF': 'Sub-Saharan Africa '}

    """

    _countriesdata = None
    _wburl = 'http://api.worldbank.org/countries?format=json&per_page=10000'
    _url = _wburl

    @staticmethod
    def set_countriesdata(data):
        # type: (Optional[List[Dict]]) -> None
        """
        Set up countries data from data in form provided by World Bank

        Args:
            data (Optional[List[Dict]]): Countries data in form provided by World Bank

        Returns:
            None
        """
        Country._countriesdata = dict()
        Country._countriesdata['countries'] = dict()
        Country._countriesdata['iso2iso3'] = dict()
        Country._countriesdata['countrynames2iso3'] = dict()
        Country._countriesdata['regions2countries'] = dict()
        Country._countriesdata['regionids2names'] = dict()
        Country._countriesdata['regionnames2ids'] = dict()
        for country in data:
            if country['region']['value'] != 'Aggregates':
                iso2 = country['iso2Code'].upper()
                iso3 = country['id'].upper()
                countryname = country['name']
                regionid = country['region']['id']
                regionname = country['region']['value']
                Country._countriesdata['countries'][iso3] = country
                Country._countriesdata['iso2iso3'][iso2] = iso3
                Country._countriesdata['countrynames2iso3'][countryname.upper()] = iso3
                region = Country._countriesdata['regions2countries'].get(regionid)
                if region is None:
                    region = set()
                    Country._countriesdata['regions2countries'][regionid] = region
                region.add(iso3)
                Country._countriesdata['regionids2names'][regionid] = regionname
                Country._countriesdata['regionnames2ids'][regionname.upper()] = regionid
        for regionid in Country._countriesdata['regions2countries']:
            Country._countriesdata['regions2countries'][regionid] = \
                sorted(list(Country._countriesdata['regions2countries'][regionid]))

    @staticmethod
    def countriesdata(use_live=True):
        # type: (bool) -> List[Dict[Dict]]
        """
        Read countries data from World Bank API (falling back to file)

        Args:
            use_live (bool): Try to get use latest data from web rather than file in package. Defaults to True.

        Returns:
            List[Dict[Dict]]: Countries dictionaries
        """
        if Country._countriesdata is None:
            json = None
            if use_live:
                try:
                    response = Download().download(Country._url)
                    json = response.json()
                except DownloadError:
                    logger.exception('Download from API failed! Falling back to stored countries file.')
            if json is None:
                json = load_json(script_dir_plus_file('countries.json', Country))
            data = json[1]
            Country.set_countriesdata(data)
        return Country._countriesdata


    @staticmethod
    def set_data_url(url):
        # type: (Optional[str]) -> None
        """
        Set url from which to retrieve countries data. Setting it to None avoids using the network and instead uses
        the internal fallback file.

        Args:
            url (Optional[str]): Url from which to retrieve countries data. Set to None to use fallback file.

        Returns:
            None
        """
        Country._url = url

    @staticmethod
    def get_country_info_from_iso3(iso3, use_live=True, exception=None):
        # type: (str, bool, Optional[ExceptionUpperBound]) -> Optional[Dict[str]]
        """Get country information from iso3 code

        Args:
            iso3 (str): Iso 3 code for which to get country name
            use_live (bool): Try to get use latest data from web rather than file in package. Defaults to True.
            exception (Optional[ExceptionUpperBound]): An exception to raise if country not found. Defaults to None.

        Returns:
            Optional[Dict[str]]: country information
        """
        countriesdata = Country.countriesdata(use_live=use_live)
        country = countriesdata['countries'].get(iso3.upper())
        if country is not None:
            return country

        if exception is not None:
            raise exception
        return None

    @staticmethod
    def get_country_name_from_iso3(iso3, use_live=True, exception=None):
        # type: (str, bool, Optional[ExceptionUpperBound]) -> Optional[str]
        """Get country name from iso3 code

        Args:
            iso3 (str): Iso 3 code for which to get country name
            use_live (bool): Try to get use latest data from web rather than file in package. Defaults to True.
            exception (Optional[ExceptionUpperBound]): An exception to raise if country not found. Defaults to None.

        Returns:
            Optional[str]: country name
        """
        countryinfo = Country.get_country_info_from_iso3(iso3, use_live=use_live, exception=exception)
        if countryinfo is not None:
            return countryinfo['name']
        return None

    @staticmethod
    def get_iso3_from_iso2(iso2, use_live=True, exception=None):
        # type: (str, bool, Optional[ExceptionUpperBound]) -> Optional[str]
        """Get iso3 from iso2 code

        Args:
            iso2 (str): Iso 2 code for which to get country name
            use_live (bool): Try to get use latest data from web rather than file in package. Defaults to True.
            exception (Optional[ExceptionUpperBound]): An exception to raise if country not found. Defaults to None.

        Returns:
            Optional[str]: Iso 3 code
        """
        countriesdata = Country.countriesdata(use_live=use_live)
        iso3 = countriesdata['iso2iso3'].get(iso2.upper())
        if iso3 is not None:
            return iso3

        if exception is not None:
            raise exception
        return None

    @staticmethod
    def get_country_info_from_iso2(iso2, use_live=True, exception=None):
        # type: (str, bool, Optional[ExceptionUpperBound]) -> Optional[Dict[str]]
        """Get country name from iso2 code

        Args:
            iso2 (str): Iso 2 code for which to get country name
            use_live (bool): Try to get use latest data from web rather than file in package. Defaults to True.
            exception (Optional[ExceptionUpperBound]): An exception to raise if country not found. Defaults to None.

        Returns:
            Optional[Dict[str]]: country information
        """
        iso3 = Country.get_iso3_from_iso2(iso2, use_live=use_live, exception=exception)
        if iso3 is not None:
            return Country.get_country_info_from_iso3(iso3, exception=exception)
        return None

    @staticmethod
    def get_country_name_from_iso2(iso2, use_live=True, exception=None):
        # type: (str, bool, Optional[ExceptionUpperBound]) -> Optional[str]
        """Get country name from iso2 code

        Args:
            iso2 (str): Iso 2 code for which to get country name
            use_live (bool): Try to get use latest data from web rather than file in package. Defaults to True.
            exception (Optional[ExceptionUpperBound]): An exception to raise if country not found. Defaults to None.

        Returns:
            Optional[str]: country name
        """
        iso3 = Country.get_iso3_from_iso2(iso2, use_live=use_live, exception=exception)
        if iso3 is not None:
            return Country.get_country_name_from_iso3(iso3, exception=exception)
        return None

    @staticmethod
    def get_iso3_country_code(country, use_live=True, exception=None):
        # type: (str, bool, Optional[ExceptionUpperBound]) -> Optional[str]
        """Get iso 3 code for country. Only exact matches or None are returned.

        Args:
            country (str): Country for which to get iso 3 code
            use_live (bool): Try to get use latest data from web rather than file in package. Defaults to True.
            exception (Optional[ExceptionUpperBound]): An exception to raise if country not found. Defaults to None.

        Returns:
            Optional[str]: Return iso 3 country code or None
        """
        countriesdata = Country.countriesdata(use_live=use_live)
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

        if exception is not None:
            raise exception
        return None

    @staticmethod
    def get_iso3_country_code_partial(country, use_live=True, exception=None):
        # type: (str, bool, Optional[ExceptionUpperBound]) -> Tuple[[Optional[str], bool]]
        """Get iso 3 code for country. A tuple is returned with the first value being the iso 3 code and the second
        showing if the match is exact or not.

        Args:
            country (str): Country for which to get iso 3 code
            use_live (bool): Try to get use latest data from web rather than file in package. Defaults to True.
            exception (Optional[ExceptionUpperBound]): An exception to raise if country not found. Defaults to None.

        Returns:
            Tuple[[Optional[str], bool]]: Return iso 3 code and if the match is exact or (None, False).
        """
        countriesdata = Country.countriesdata(use_live=use_live)
        iso3 = Country.get_iso3_country_code(country)  # don't put exception param here as we don't want it to throw

        if iso3 is not None:
            return iso3, True

        countryupper = country.upper()
        for countryname in countriesdata['countrynames2iso3']:
            if countryupper in countryname or countryname in countryupper:
                return countriesdata['countrynames2iso3'][countryname], False

        if exception is not None:
            raise exception
        return None, False

    @staticmethod
    def get_countries_in_region(region, use_live=True, exception=None):
        # type: (str, bool, Optional[ExceptionUpperBound]) -> List[str]
        """Get countries (iso 3 codes) in continent

        Args:
            region (str): Three letter region code or region name
            use_live (bool): Try to get use latest data from web rather than file in package. Defaults to True.
            exception (Optional[ExceptionUpperBound]): An exception to raise if region not found. Defaults to None.

        Returns:
            List(str): Sorted list of iso 3 country names
        """
        countriesdata = Country.countriesdata(use_live=use_live)
        regionupper = region.upper()
        if regionupper in countriesdata['regionids2names']:
            return countriesdata['regions2countries'][regionupper]
        regionid = countriesdata['regionnames2ids'].get(regionupper)
        if regionid is not None:
            return countriesdata['regions2countries'][regionid]

        if exception is not None:
            raise exception
        return list()
