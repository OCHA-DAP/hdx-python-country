import string
import unicodedata


def make_replace_mapping():
    chars_to_replace = [string.ascii_uppercase]
    replacement_chars = [string.ascii_lowercase]
    #    punctuation = string.punctuation.replace("'", "")
    #    chars_to_replace.append(punctuation)
    #    replacement_chars.append(" " * len(punctuation))
    #    chars_to_replace.append(string.whitespace)
    #    replacement_chars.append(" " * len(string.whitespace))

    chars_to_replace = "".join(chars_to_replace)
    replacement_chars = "".join(replacement_chars)
    return str.maketrans(chars_to_replace, replacement_chars)  # , "'")


replacement_mapping = make_replace_mapping()


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
    for x in unicodedata.normalize("NFD", name):
        ordch = ord(x)
        if 97 <= ordch < 123:
            chars.append(x)
        elif 65 <= ordch < 91:
            chars.append(chr(ordch + 32))
        elif ordch < 32 or ordch >= 127:
            continue
        else:
            chars.append(x)
    return "".join(chars).strip()
