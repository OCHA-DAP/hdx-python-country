# -*- coding: utf-8 -*-
"""Update fallback file country_data.tsv"""
from os.path import join

from hdx.utilities.downloader import Download
from hdx.utilities.path import script_dir


def main():
    url = 'https://raw.githubusercontent.com/konstantinstadler/country_converter/master/country_converter/country_data.tsv'
    folder = join(script_dir(main), 'src', 'hdx', 'location')
    file = 'country_data.tsv'
    with Download() as downloader:
        downloader.download_file(url, folder, file, overwrite=True)


if __name__ == "__main__":
    main()
