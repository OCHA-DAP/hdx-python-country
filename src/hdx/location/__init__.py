# -*- coding: utf-8 -*-
import re
import unicodedata

import six
from unidecode import unidecode

non_ascii = '([^\x00-\x7F])+'


def clean_name(name):
    # Replace accented characters with non accented ones
    clean_name = ''.join((c for c in unicodedata.normalize('NFD', six.u(name)) if unicodedata.category(c) != 'Mn'))
    # Remove all non-ASCII characters
    clean_name = re.sub(non_ascii, ' ', clean_name)
    clean_name = unidecode(clean_name)
    return clean_name.strip().lower()


def get_phonetics():
    if six.PY2:
        class Phonetics_Py2(object):
            def match(self, possible_names, name, alternative_name=None, transform_possible_names=list(), threshold=2):
                return None
        return Phonetics_Py2()
    else:
        from hdx.location.phonetics import Phonetics
        return Phonetics()
