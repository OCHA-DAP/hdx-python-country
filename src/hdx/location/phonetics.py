from typing import Callable, Optional

from rapidfuzz import fuzz

from hdx.location.names import remove_whitespace
from hdx.utilities.typehint import ListTuple


class Phonetics:
    """
    Phonetic matching class.

    Args:
        threshold (float): Match threshold. Value is 0-100. Defaults to 60.
        try_remove_spaces (bool): Whether to also try removing spaces. Defaults to True.
    """

    def __init__(
        self, threshold: float = 60, try_remove_spaces: bool = True
    ) -> None:
        self.threshold = threshold
        self.try_remove_spaces = try_remove_spaces

    def match(
        self,
        possible_names: ListTuple,
        name: str,
        alternative_name: Optional[str] = None,
        transform_possible_names: ListTuple[Callable] = [],
    ) -> Optional[int]:
        """
        Match name to one of the given possible names. Returns None if no match
        or the index of the matching name

        Args:
            possible_names (ListTuple): Possible names
            name (str): Name to match
            alternative_name (str): Alternative name to match. Defaults to None.
            transform_possible_names (ListTuple[Callable]): Functions to transform possible names.

        Returns:
            Optional[int]: Index of matching name from possible names or None
        """
        max_similarity = 0
        matching_index = None

        transform_possible_names.insert(0, lambda x: x)

        def check_name(name, possible_name):
            nonlocal max_similarity, matching_index  # noqa: E999

            similarity = fuzz.token_sort_ratio(name, possible_name)
            if similarity > max_similarity:
                max_similarity = similarity
                matching_index = i

        names_to_match = [name]
        if self.try_remove_spaces:
            no_whitespace = remove_whitespace(name)
            if no_whitespace != name:
                names_to_match.append(no_whitespace)
        if alternative_name != name:
            names_to_match.append(alternative_name)
            if self.try_remove_spaces:
                no_whitespace = remove_whitespace(alternative_name)
                if no_whitespace != alternative_name:
                    names_to_match.append(no_whitespace)

        for i, possible_name in enumerate(possible_names):
            for transform_possible_name in transform_possible_names:
                transformed_possible_name = transform_possible_name(
                    possible_name
                )
                if not transformed_possible_name:
                    continue
                for name in names_to_match:
                    check_name(name, transformed_possible_name)
                if not self.try_remove_spaces:
                    continue
                no_whitespace = remove_whitespace(transformed_possible_name)
                if no_whitespace == transformed_possible_name:
                    continue
                for name in names_to_match:
                    check_name(name, no_whitespace)

        if max_similarity < self.threshold:
            return None
        return matching_index
