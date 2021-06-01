import sys

if sys.version_info[0] == 2:
    class Phonetics(object):
        def match(self, possible_names, name):
            return None, None
else:
    import pyphonetics

    class Phonetics(pyphonetics.RefinedSoundex):
        def match(self, possible_names, name, alternative_name=None, transform_possible_names=list(), threshold=2):
            mindistance = None
            matching_index = None

            transform_possible_names.insert(0, lambda x: x)

            def check_name(name, possible_name):
                nonlocal mindistance, matching_index

                distance = self.distance(name, possible_name)
                if mindistance is None or distance < mindistance:
                    mindistance = distance
                    matching_index = i

            for i, possible_name in enumerate(possible_names):
                for transform_possible_name in transform_possible_names:
                    transformed_possible_name = transform_possible_name(possible_name)
                    if not transformed_possible_name:
                        continue
                    check_name(name, transformed_possible_name)
                    if alternative_name:
                        check_name(alternative_name, transformed_possible_name)
            if mindistance is None or mindistance > threshold:
                return None
            return matching_index
