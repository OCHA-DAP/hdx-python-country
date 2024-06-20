from typing import Callable, Optional

from rapidfuzz import fuzz

from hdx.utilities.typehint import ListTuple


class Phonetics:
    def match(
        self,
        possible_names: ListTuple,
        name: str,
        alternative_name: Optional[str] = None,
        transform_possible_names: ListTuple[Callable] = [],
        threshold: float = 60,
    ) -> Optional[int]:
        """
        Match name to one of the given possible names. Returns None if no match
        or the index of the matching name

        Args:
            possible_names (ListTuple): Possible names
            name (str): Name to match
            alternative_name (str): Alternative name to match. Defaults to None.
            transform_possible_names (ListTuple[Callable]): Functions to transform possible names.
            threshold (float): Match threshold. Value is 0-100. Defaults to 60.

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

        for i, possible_name in enumerate(possible_names):
            for transform_possible_name in transform_possible_names:
                transformed_possible_name = transform_possible_name(
                    possible_name
                )
                if not transformed_possible_name:
                    continue
                check_name(name, transformed_possible_name)
                if alternative_name:
                    check_name(alternative_name, transformed_possible_name)
        if max_similarity < threshold:
            return None
        return matching_index
