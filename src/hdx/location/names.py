import re
import unicodedata

from unidecode import unidecode

non_ascii = "([^\x00-\x7F])+"


def clean_name(name: str) -> str:
    """
    Replace accented characters with non-accented ones in given name. Also
    strip whitespace from start and end and make lwoercase.

    Args:
        name (str): Name to change

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
    clean_name = unidecode(clean_name)
    return clean_name.strip().lower()
