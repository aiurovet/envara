###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# Filtering for DotEnv
###############################################################################


import re
from typing import ClassVar

from env import Env

###############################################################################
# Implementation
###############################################################################


class DotEnvFilter:
    # Default regex flags to compile with
    DEFAULT_RE_FLAGS: ClassVar[re.RegexFlag] = re.RegexFlag.IGNORECASE

    # Regex to strip all unnecessary blanks around every delimited field
    DEFAULT_STRIP_RE: ClassVar[re.Pattern] = re.compile(r"^\s+|\s*(,)\s*|\s+$")

    def __init__(
        self,
        ind: str | None,
        cur: list[str] | str | None = None,
        all: list[str] | str | None = None
    ):
        """
        Constructor
        
        :param self: The object
        :param ind: indicator - a necessary part, default: 'env'
        :type ind: str | None
        :param cur: One or more strings relevant to the current run passed
                    either as a list of strings or as a single string
        :type cur: list[str] | str | None
        :param all: All possible values passed as a list of strings
        :type all: list[str]
        """
        # Accept input data
    
        self.all = all
        self.cur = cur

        # Parse input data into regular expressions
    
        self.all_regex = DotEnvFilter.to_regex(ind, all);
        self.cur_regex = DotEnvFilter.to_regex(ind, cur);

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

        return not self.all_regex.search(input)

    ###########################################################################

    @staticmethod
    def to_regex(
        src: list[str] | str | None,
        ind: str | None = None
    ) -> re.Pattern:
        """
        Attach delimiters to input items, create patterns and append
        those to the target list
      
        :param ind: indicator - a part to be always present, if None, then
            set as the default one
        :type ind: str | None
        :param input: comma-separated string or a list of input filters
            with optional wildcards: "linux,*os" or ["en", "es", "fr"] or
            "dev,*test*,prod*"
        :type input: str
        """

        # Ensure the indicator is a valid string

        if ind is None:
            ind = "env"

        # Define a pattern for all allowed separators as well as a minimum
        # pattern (if the indicator is not empty)

        sep: str = r"[\.\-_]"
        min: str = f"^{sep}*{ind}{sep}*$" if ind else ""

        # If input filters are not present, add the default regex and finish

        if not src:
            return re.compile(min, flags=DotEnvFilter.DEFAULT_RE_FLAGS) \
                if min else None

        # Convert glob pattern to a regular expression pattern

        if isinstance(src, list):
            src = ",".join(src)

        # Remove all unnecessary blanks around every delimited field

        src = DotEnvFilter.DEFAULT_STRIP_RE.sub(r"\1", src)

        # Define side and middle separator patterns

        lft: str = f"(^|{sep})"
        mid: str = f"({sep}+|{sep}+.+{sep}+)"
        rgt: str = f"({sep}|$)"

        # Convert glob pattern to regex pattern

        pat: str = DotEnvFilter.__limited_glob_str_to_regex_str(src)

        # Compose the final pattern, compile that into a regular expression
        # and append to the target list

        if min:
            pat = f"{min}|{lft}{ind}{mid}{pat}{rgt}|{lft}{pat}{mid}{ind}{rgt}"
        else:
            pat = f"{lft}{pat}{rgt}"

        return re.compile(pat, flags=DotEnvFilter.DEFAULT_RE_FLAGS)

    ###########################################################################

    @staticmethod
    def __limited_glob_str_to_regex_str(
        input: str | None,
        is_full: bool = False
    ) -> str:
        """
        Convert a limited glob pattern string into a regular expression
        pattern string using comma, asterisk and curly brackets only, no
        escaping, caret and dollar sign are not added if is_full = False:
        ```
            'dev,test,prod' => '^(dev|test|prod)$'
            'dev*,test,prod*' => '^(dev.*|test|prod)$'
            '{en,es,fr,jp}?' => '^(en|es|fr).$'
        ```
        :param input: a string to convert
        :type input: str | None
        :param is_full: if True, full string match is required: `^(...)$`
        :type is_full: bool
        :return: input converted to a regular expression pattern string
        :rtype: str
        """

        if input is None:
            input = ""

        return ("^(" if is_full else "(") + \
            re.escape(input) \
                .replace(",", "|") \
                .replace("\\{", "(") \
                .replace("\\}", ")") \
                .replace("\\?", ".") \
                .replace("\\*", ".*") + \
            (")$" if is_full else ")")


###############################################################################
