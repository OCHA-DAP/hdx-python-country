from typing import Callable, Optional

import pyphonetics

from hdx.utilities.typehint import ListTuple


class Phonetics(pyphonetics.RefinedSoundex):
    def match(
        self,
        possible_names: ListTuple,
        name: str,
        alternative_name: Optional[str] = None,
        transform_possible_names: ListTuple[Callable] = [],
        threshold: int = 2,
    ) -> Optional[int]:
        """
        Match name to one of the given possible names. Returns None if no match
        or the index of the matching name

        Args:
            possible_names (ListTuple): Possible names
            name (str): Name to match
            alternative_name (str): Alternative name to match. Defaults to None.
            transform_possible_names (ListTuple[Callable]): Functions to transform possible names.
            threshold: Match threshold. Defaults to 2.

        Returns:
            Optional[int]: Index of matching name from possible names or None
        """
        mindistance = None
        matching_index = None

        transform_possible_names.insert(0, lambda x: x)

        def check_name(name, possible_name):
            nonlocal mindistance, matching_index  # noqa: E999

            distance = self.distance(name, possible_name)
            if mindistance is None or distance < mindistance:
                mindistance = distance
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
        if mindistance is None or mindistance > threshold:
            return None
        return matching_index
