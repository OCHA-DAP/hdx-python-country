import string
import unicodedata


def make_replace_mapping():
    chars_to_replace = [string.ascii_uppercase]
    replacement_chars = [string.ascii_lowercase]
    #    punctuation = string.punctuation.replace("'", "")
    #    chars_to_replace.append(punctuation)
    #    replacement_chars.append(" " * len(punctuation))
    chars_to_replace.append(string.whitespace)
    replacement_chars.append(" " * len(string.whitespace))

    chars_to_replace = "".join(chars_to_replace)
    replacement_chars = "".join(replacement_chars)
    return str.maketrans(chars_to_replace, replacement_chars)  # , "'")


replacement_mapping = make_replace_mapping()

lowercase_space = string.ascii_lowercase + string.punctuation + string.digits + " "


map_to_space = {9, 10, 11, 12, 13, 32, 47}


def clean_name(name: str) -> str:
    """
    Replace accented characters with non-accented ones in given name. Also
    strip whitespace from start and end and make lowercase.

    Args:
        name (str): Name to change

    Returns:
        str: Name without accented characters
    """
    # Replace all non-ASCII characters with equivalent if available or remove
    chars = []
    space = False
    for x in unicodedata.normalize("NFD", name):
        match ord(x):
            case num if 97 <= num < 123:
                chars.append(x)
                space = False
            case num if 65 <= num < 91:
                chars.append(chr(num + 32))
                space = False
            case num if num in map_to_space:
                if space:
                    continue
                chars.append(" ")
                space = True
            case num if 33 <= num < 127:
                chars.append(x)
                space = False
            case _:
                continue
    return "".join(chars).strip()
