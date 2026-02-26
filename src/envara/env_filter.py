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

    def __init__(
        self,
        indicator: str = DEFAULT_INDICATOR,
        cur_values: list[str] | str | None = None,
        all_values: list[str] | str | None = None,
    ):
        """
        Constructor

        :param self: The object

        :param indicator: A necessary part of a name (always present),
            default: DEFAULT_INDICATOR
        :type indicator: str | None

        :param cur_values: One or more strings relevant to the current run
            passed either as a list of strings or as a single string
        :type cur_values: list[str] | str | None

        :param all_values: All possible values passed as a list of strings
        :type all_values: list[str]
        """
        # Accept parameters

        self.indicator = indicator
        self.all_values = all_values
        self.cur_values = cur_values

        # Parse pattern-related parameters into regular expressions

        self.ind_regex = EnvFilter.to_regex(indicator, is_full=False)
        self.all_regex = EnvFilter.to_regex(indicator, all_values)
        self.cur_regex = EnvFilter.to_regex(indicator, cur_values)

    ###########################################################################

    def is_match(
        self,
        input: list[str] | str | None,
    ) -> bool:
        """
        Check the input matches given filters:

        - should match the default one
        - should either match the current one or not match the whole set at
          all: `.en.prod` should match `.env.en`, `fr.env` and `_jp_env`,
          but neither `.prod.es`, nor `.es_prod` matches
        """
        if self.cur_regex.search(input):
            return True

        if not self.ind_regex.search(input):
            return False

        return not self.all_regex.search(input)

    ###########################################################################

    @staticmethod
    def to_regex(
        indicator: str = DEFAULT_INDICATOR,
        input: list[str] | str | None = None,
        is_full: bool = True,
    ) -> re.Pattern:
        """
        Convert glob or regex pattern string into regex

        :param indicator: Required part of a name (always present),
            default: DEFAULT_INDICATOR
        :type indicator: str | None

        :param input: Comma-separated string or a list of strings with the
           optional wildcards: "linux,*os" or ["en", "es", "fr"] or
           "dev,*test*,prod*"
        :type input: str

        :param is_full: True = wrap into ^...$
        :type is_full: bool

        :return: Regular expression matching passed critera
        :rtype: re.Pattern
        """

        # Ensure the indicator is a valid string

        ind: str = EnvFilter.DEFAULT_INDICATOR if indicator is None else indicator

        # Define a pattern for all allowed separators as well as a minimum
        # pattern (if the indicator is not empty)

        sep: str = r"[\.\-_]"

        # Define a minimum pattern (if the indicator is not empty)

        min: str = ""

        if ind:
            min = f"{sep}*{ind}{sep}*"
            if is_full:
                min = f"^{min}$"

        # If input filters are not present, add the default regex and finish

        if not input:
            return re.compile(min, flags=EnvFilter.DEFAULT_RE_FLAGS) if min else None

        # If input is a list, join it's elements into a string, but if
        # input looks like a regular exprssion pattern string, compile that
        # and return

        if isinstance(input, list):
            input = ",".join(input)

        # Remove all unnecessary blanks around every delimited field

        input = EnvFilter.DEFAULT_STRIP_RE.sub(r"\1", input)

        # Define side and middle separator patterns

        lft: str = f"(?:^|{sep})"
        mid: str = f"(?:{sep}+|{sep}+.+{sep}+)"
        rgt: str = f"(?:{sep}|$)"

        # Convert glob pattern to regex pattern

        pat: str = EnvFilter.__limited_glob_str_to_regex_str(input)

        # Compose the final pattern, compile that into a regular expression
        # and append to the target list

        if min:
            pat = f"{min}|{lft}{ind}{mid}{pat}{rgt}|{lft}{pat}{mid}{ind}{rgt}"
        else:
            pat = f"{lft}{pat}{rgt}"

        return re.compile(pat, flags=EnvFilter.DEFAULT_RE_FLAGS)

    ###########################################################################

    @staticmethod
    def __limited_glob_str_to_regex_str(
        input: str | None, is_full: bool = False
    ) -> str:
        """
        Convert a limited glob pattern string into a regular expression
        pattern string using comma, asterisk and curly brackets only, no
        escaping, caret and dollar sign are not added if is_full = False.
        However, if the input looks like a regular expression pattern
        string, return that unchanged ignoring is_full:
        ```
            'dev|test|prod' => 'dev|test|prod'
            'dev,test,prod' => '^(dev|test|prod)$'
            'dev*,test,prod*' => '^(dev.*|test|prod)$'
            '{en,es,fr,jp}?' => '^(en|es|fr).$'
        ```
        :param input: String to convert
        :type input: str | None
    
        :param is_full: if True, full string match is required: `^(...)$`
        :type is_full: bool
    
        :return: input converted to a regular expression pattern string
        :rtype: str
        """

        # Coalesce for validity of string operations

        if input is None:
            input = ""

        # If the input looks like a regular expression pattern string,
        # return that unchanged

        inp_len: int = len(input)

        if (inp_len > 1) and (
            ("|" in input)
            or ("(" in input)
            or ("^" == input[0])
            or ("$" == input[inp_len - 1])
        ):
            return input if input[0] in "^(" else f"(?:{input})"

        return (
            ("^(?:" if is_full else "(?:")
            + re.escape(input)
            .replace(",", "|")
            .replace(r"\{", "(?:")
            .replace(r"\}", ")")
            .replace(r"\[!", "[^")
            .replace(r"\[", "[")
            .replace(r"\]", "]")
            .replace(r"\^", "^")
            .replace(r"\?", ".")
            .replace(r"\*", ".*")
            + (")$" if is_full else ")")
        )


###############################################################################
