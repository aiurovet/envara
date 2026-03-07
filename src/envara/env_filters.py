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
        Filter and sort the input list of strings according to filters, and
        in the order those appear. In a highly unlikely event of no difference
        found, a mere case-sensitive string comparison engaged

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
            cur_2 = -1

            for cur_1 in indices_1:
                cur_2 = cur_2 + 1
                dif = cur_1 - indices_2[cur_2]
                if dif != 0:
                    return dif

            if item1 == item2:
                return 0

            if item1 < item2:
                return -1

            return 1

        # Sort the filtered items and return

        return sorted(filtered, key=cmp_to_key(compare_items))


###############################################################################
