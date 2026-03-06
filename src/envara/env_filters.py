###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# Environment-related filtering helpers (mainly, for EnvFile)
###############################################################################

from functools import cmp_to_key

from envara.env_filter import EnvFilter

###############################################################################
# Implementation
###############################################################################


class EnvFilters:

    @staticmethod
    def process(
        input: list[str],
        filters: list[EnvFilter],
    ) -> list[str]:
        """
        Filter and sort the input list of strings according to filters:

        :param input: The input list to filter and sort
        :type input: list[str]

        :param filters: The list of filters to apply
        :type filters: list[EnvFilter]

        :return: The final list
        :rtype: list[str]
        """

        # Check empty parameters

        if (not filters) or (not input) or (len(input) <= 0):
            return input

        # Initialize the output list

        filtered: list[str] = []
        indices: dict[str, list[int]] = {}

        # Accumulate indices of all relevant items from the input

        for item in input:
            is_match: bool = True
            item_indices: list[int] = []

            for filter in filters:
                i = filter.search(item)
                if i < 0:
                    is_match = False
                    break
                item_indices.append(i)

            if is_match:
                filtered.append(item)
                indices[item] = item_indices

        # Define complex comparer for sorting

        def compare_items(item1: str, item2: str):
            indices_1 = indices[item1]
            indices_2 = indices[item2]
            i = -1

            for index_1 in indices_1:
                i = i + 1
                d = index_1 - indices_2[i]
                if d != 0:
                    return d

            return 0

        # Sort the filtered items and return

        return sorted(filtered, key=cmp_to_key(compare_items))


###############################################################################
