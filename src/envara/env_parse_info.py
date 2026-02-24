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

    POSIX_EXPAND_CHAR: ClassVar[str] = "$"
    POSIX_ESCAPE_CHAR: ClassVar[str] = "\\"

    PWSH_EXPAND_CHAR: ClassVar[str] = POSIX_EXPAND_CHAR
    PWSH_ESCAPE_CHAR: ClassVar[str] = "`"

    WINDOWS_EXPAND_CHAR: ClassVar[str] = "%"
    WINDOWS_ESCAPE_CHAR: ClassVar[str] = "^"

    ###########################################################################

    def __init__(
        self,
        input: str | None = None,
        result: str | None = None,
        expand_char: str | None = None,
        escape_char: str | None = None,
        quote_type: EnvQuoteType = EnvQuoteType.NONE,
    ):
        """
        Constructor

        :param self: The object
        :param input: String being unquoted
        :type input: str
        :param result: Result of unquoting
        :type result: str
        :param expand_char: First active expand character encountered
                        (e.g., "$", "%", "<")
        :type expand_char: str
        :param escape_char: First active escape character encountered
                        (e.g., "\\\\", "`", "^")
        :type escape_char: str
        :param quote_type: Type of enclosing quotes found
        :type quote_type: EnvQuoteType
        """

        self.expand_char: str = expand_char
        self.escape_char: str = escape_char
        self.input: str = input
        self.quote_type: EnvQuoteType = quote_type
        self.result: str = result


###############################################################################
