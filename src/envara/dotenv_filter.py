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
    DEFAULT_RE_FLAGS: ClassVar[re.RegexFlag] = re.RegexFlag.IGNORECASE

    def __init__(
        self,
        cur: list[str] | str | None = None,
        all: list[str] | str | None = None
    ):
        """
        Constructor
        
        :param self: The object
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
    
        self.all_regex = DotEnvFilter.to_regex(all);
        self.cur_regex = DotEnvFilter.to_regex(cur);

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

        if not DotEnvFilter.DEFAULT_RE.search(input):
            return False

        return not self.all_regex.search(input)

    ###########################################################################

    @staticmethod
    def to_regex(
        input: list[str] | str | None,
    ) -> re.Pattern:
        """
        Attach delimiters to input items, create patterns and append
        those to the target list
      
        :param target: destination list of regexi
        :type target: list[re.Pattern]
        :param input: comma-separated input filters with optional wildcards:
                       "linux,*os" or "en,es,fr" or "dev,*test*,prod*"
        :type input: str
        """

        # Making variable name shorter for better clarity

        i: str = f"(env)"

        # Define a pattern for all allowed separators as well as default
        # filename pattern

        s: str = r"[\.\-_]"

        # If input filters are not present, add the default regex and finish

        if not input:
            p: str = f"^{s}*{i}$"
            return re.compile(p, flags=DotEnvFilter.DEFAULT_RE_FLAGS)

        # Convert glob pattern to a regular expression pattern

        if isinstance(input, list):
            input = ",".join(input)

        x: str = DotEnvFilter.__limited_glob_str_to_regex_str(input)

        # Compose the final pattern, compile that into a regular expression
        # and append to the target list

        p: str = f"(^|{s}){x}({s}|$)"
        return re.compile(p, flags=DotEnvFilter.DEFAULT_RE_FLAGS)

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
