###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# Environment-related filtering (mainly, for EnvFile)
###############################################################################


import re
from typing import ClassVar

###############################################################################
# Implementation
###############################################################################


class EnvFilter:
    DEFAULT_RE_FLAGS: ClassVar[re.RegexFlag] = re.RegexFlag.IGNORECASE
    """Default regex flags to compile with"""

    DEFAULT_INDICATOR: ClassVar[str] = "env"
    """Default dot-env file type without leading extension separator"""

    DEFAULT_STRIP_RE: ClassVar[re.Pattern] = re.compile(r"^\s+|\s*(,)\s*|\s+$")
    """Regex to strip all unnecessary blanks around every delimited field"""

    VALUE_SEPARATORS: ClassVar[str] = ".-_"
    """Any of these characters separates values in an input string"""

    def __init__(
        self,
        indicator: str | None = None,
        cur_values: list[str] | None = None,
        all_values: list[str] | None = None,
    ):
        """
        Constructor

        :param self: The object

        :param indicator: Nnecessary part of a name (always present),
            default: DEFAULT_INDICATOR
        :type indicator: str | None

        :param cur_values: List of zero, one or more strings representing
            all available values for this machine and OS and run
        :type cur_values: list[str] | None

        :param all_values: List of all theoretically possible f string values
            regradless of this machine, OS and run
        :type all_values: list[str]
        """
        # Accept parameters

        self.indicator = EnvFilter.DEFAULT_INDICATOR if indicator is None else indicator

        self.cur_values = cur_values
        self.all_values = all_values or self.cur_values

    ###########################################################################

    @staticmethod
    def has_value(
        input: str | None,
        value: str | None,
    ) -> tuple[bool, bool]:
        """
        Search input for value surrounded by separators or at the edge:

        :param input: String to search value for
        :type input: str | None

        :param value: String to search in the input
        :type value: str | None

        :return: (is_found, are_equal)
        :rtype: tuple[bool, bool]
        """

        # Initialise the output flag if required

        # If input or value is empoty or None, then not found

        if not input or not value:
            return (False, False)

        # Get length of input and value

        inp_len: int = len(input)
        val_len: int = len(value)

        # If input is shorter than value, then not found

        if inp_len < val_len:
            return (False, False)

        # If input is of the same length as value, then
        # found if and only if they are the same

        if inp_len == val_len:
            return (True, True) if input == value else (False, False)

        # Initialize loop variables

        curr_pos: int = -1
        last_pos: int = inp_len - 1
        next_pos: int = curr_pos + 1

        # Loop through every occurrence of value, and when it is
        # surrounded with separators or edges, then found

        while True:
            curr_pos = input.find(value, next_pos)

            if curr_pos < 0:
                return (False, False)

            next_pos = curr_pos + val_len

            if (curr_pos == 0) or (
                (curr_pos > 0) and (input[curr_pos - 1] in EnvFilter.VALUE_SEPARATORS)
            ):
                if next_pos > last_pos:
                    return (True, curr_pos <= 1)
                if input[next_pos] in EnvFilter.VALUE_SEPARATORS:
                    return (True, ((next_pos == last_pos) and (curr_pos <= 1)))

            curr_pos = next_pos

    ###########################################################################

    def search(
        self,
        input: str | None,
    ) -> int:
        """
        Find matching item no for the input string. Requirements:

        - the indicator should be found if non-empty
        - either one of the current values should be found or none of
          all values (i.e.'any'): assuming runtime environments include
          'dev', 'test' and 'prod', then '.env', '.env.en.prod`,
          `fr-prod.env` and `prod_jp_env` should be found, but neither
          `.env.dev`, `.env.dev.en`, nor `en_test.env`, nor `test-env`

        :param self: The object
        :type: EnvFilter

        :param input: the string to match against current and all values
        :type input: str

        :return: Last matching group no or -1 if failed
        :rtype: int
        """

        # If indicator found, and is equal to input, return 0
        # If indicator is not found, return -1 (not found)

        is_found, are_equal = EnvFilter.has_value(input, self.indicator)

        if is_found:
            if are_equal:
                return 0
        else:
            return -1

        # Initialize cur_values count as well as index related to position
        # in the cur_values list

        cur_index: int = 0
        found_index: int = -1

        # Find the first matching value

        for x in self.cur_values:
            cur_index = cur_index + 1
            if EnvFilter.has_value(input, x)[0]:
                found_index = cur_index
                break

        # If the first matching value found return respective index

        if found_index >= 0:
            return found_index

        # Check whether input is in scope at all

        in_scope = any(EnvFilter.has_value(input, x)[0] for x in self.all_values)

        # If input is not in scope, then top match. Otherwise, not found

        return -1 if in_scope else 0


###############################################################################
