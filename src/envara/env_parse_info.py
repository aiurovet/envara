###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# String unquoting details
###############################################################################

from typing import ClassVar
from env_quote_type import EnvQuoteType


###############################################################################


class EnvParseInfo:
    """
    Details of what was found in a string while removing quotes as well as
    that string and the result of its unquoting
    """

    # Pre-defined constants

    POSIX_CUTTER_CHAR: ClassVar[str] = "#"
    POSIX_EXPAND_CHAR: ClassVar[str] = "$"
    POSIX_ESCAPE_CHAR: ClassVar[str] = "\\"

    PWSH_CUTTER_CHAR: ClassVar[str] = "#"
    PWSH_EXPAND_CHAR: ClassVar[str] = POSIX_EXPAND_CHAR
    PWSH_ESCAPE_CHAR: ClassVar[str] = "`"

    WINDOWS_CUTTER_CHAR: ClassVar[str] = ";"
    WINDOWS_EXPAND_CHAR: ClassVar[str] = "%"
    WINDOWS_ESCAPE_CHAR: ClassVar[str] = "^"

    ###########################################################################

    def __init__(
        self,
        input: str | None = None,
        result: str | None = None,
        expand_char: str | None = None,
        escape_char: str | None = None,
        cutter_char: str | None = None,
        quote_type: EnvQuoteType = EnvQuoteType.NONE,
    ):
        """
        Constructor

        :param self: the object

        :param input: string being unquoted
        :type input: str

        :param result: result of unquoting
        :type result: str

        :param expand_char: first non-escaped and non-quoted expand character
            encountered: dollar, percent, angle bracket
        :type expand_char: str

        :param escape_char: first non-escaped and non-quoted character
            encountered: backslash, backtick, caret
        :type escape_char: str

        :param quote_type: Type of enclosing quotes found
        :type quote_type: EnvQuoteType
        """

        self.expand_char: str = expand_char
        self.escape_char: str = escape_char
        self.cutter_char: str = cutter_char
        self.input: str = input
        self.quote_type: EnvQuoteType = quote_type
        self.result: str = result


###############################################################################
