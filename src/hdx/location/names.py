import re
import unicodedata

from unidecode import unidecode

non_ascii = r"([^\x00-\x7f])+"


def remove_whitespace(name: str) -> str:
    """
    Remove whitespace from a name.

    Args:
        name (str): Name from which to remove whitespace.

    Returns:
        str: Name without spaces
    """
    return "".join(name.split())


def clean_name(name: str) -> str:
    """
    Replace accented characters with non-accented ones in given name. Also
    strip whitespace from start and end and make lowercase.

    Args:
        name (str): Name to clean

    Returns:
        str: Name without accented characters
    """
    #
    clean_name = "".join(
        c
        for c in unicodedata.normalize("NFD", name)
        if unicodedata.category(c) != "Mn"
    )
    # Remove all non-ASCII characters
    clean_name = re.sub(non_ascii, " ", clean_name)
    clean_name = re.sub(r"'+", "", clean_name)
    clean_name = re.sub(r"[\W_]+", " ", clean_name)
    clean_name = unidecode(clean_name)
    return clean_name.strip().lower()
