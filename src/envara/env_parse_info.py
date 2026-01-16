###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# String unquoting details
###############################################################################

import re
from typing import ClassVar

from env_quote_type import EnvQuoteType

###############################################################################


class EnvParseInfo:
    """
    Details of what was found in a string while removing quotes as well as
    that string and the result of its unquoting
    """

    # Pre-defined POSIX constants

    POSIX_ESCAPE: ClassVar[str] = "\\"
    POSIX_EXPAND: ClassVar[str] = "$"

    PWSH_ESCAPE: ClassVar[str] = "`"
    PWSH_EXPAND: ClassVar[str] = "$"

    WINDOWS_ESCAPE: ClassVar[str] = "^"
    WINDOWS_EXPAND: ClassVar[str] = "%"

    # Pre-defined non-POSIX constants

    DEFAULT_ESCAPES: ClassVar[str] = POSIX_ESCAPE
    DEFAULT_EXPANDS: ClassVar[str] = POSIX_EXPAND

    # Default flags used to create regexi

    DEFAULT_RE_FLAGS: ClassVar[int] = re.IGNORECASE | re.UNICODE

    # Helps to find env var/arg parttern based on expand and escape

    PATTERNS: ClassVar[dict[str, re.Pattern]] = {
        "$\\": re.compile("([\\\\]*)\\$({?)([A-Za-z_\\d]+)(}?)", DEFAULT_RE_FLAGS),
        "$`": re.compile("([``]*)\\$({?)([A-Za-z_\\d]+)(}?)", DEFAULT_RE_FLAGS),
        "%\\": re.compile("([\\\\]*)(%)([A-Za-z_\\d]+)(%)", DEFAULT_RE_FLAGS),
        "%^": re.compile("([\\^]*)(%)([A-Za-z_\\d]+)(%)", DEFAULT_RE_FLAGS),
    }

    ###########################################################################

    def __init__(
        self,
        input: str,
        result: str = None,
        escape: str = None,
        expand: str = None,
        quote_type: EnvQuoteType = EnvQuoteType.NONE
    ):
        """
        Constructor
        
        :param self: The object
        :param input: String being unquoted
        :type input: str
        :param result: Result of unquoting
        :type result: str
        :param escape: First active escape character encountered
                       (e.g., "\\\\", "`", "^")
        :type escape: str
        :param expand: First active expand character encountered
                       (e.g., "$", "%", "<")
        :type expand: str
        :param quote_type: Type of enclosing quotes found
        :type quote_type: EnvQuoteType
        """

        self.escape: str = escape or ""
        self.expand: str = expand or ""
        self.input: str = input or ""
        self.result: str = result or ""

        self.quote_type: EnvQuoteType = quote_type

        # Initialize pattern based on known data
    
        self.pattern: re.Pattern = EnvParseInfo.find_pattern(
            expand=self.expand,
            escape=self.escape,
        )

    ###########################################################################

    @staticmethod
    def find_pattern(
        expand: str = None,
        escape: str = None,
    ) -> re.Pattern:
        """
        Find pattern for environment variables' and arguments' placeholders
        
        :param patterns: collection of expand-escape => regex mappings
        :type patterns: dict[str, re.Pattern]
        :param expand: Expand character used
        :type expand: str
        :param escape: Escape character used
        :type escape: str
        :return: Regex found in the map of patterns by a given key
        :rtype: re.Pattern
        """
        # Coalesce escape if not passed

        if (escape is None):
            escape = EnvParseInfo.POSIX_ESCAPE

        # Coalesce expand if not passed

        if (expand is None):
            expand = EnvParseInfo.POSIX_EXPAND

        # If expand and escape form a valid key to the set of patterns,
        # return the found pattern. Otherwise, None

        return EnvParseInfo.PATTERNS.get(f"{expand}{escape}")

###############################################################################
