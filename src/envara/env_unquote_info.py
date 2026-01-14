###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# String unquoting details
###############################################################################

from typing import Final

from env_quote_type import EnvQuoteType

###############################################################################


class EnvUnquoteInfo:
    """
    Details of what was found in a string while removing quotes as well as
    that string and the result of its unquoting
    """

    # Pre-defined POSIX constants

    POSIX_ESCAPE: Final[str] = "\\"
    POSIX_EXPAND: Final[str] = "$"

    # Pre-defined non-POSIX constants as used in .env files under numerous
    # other OSes: Windows, OpenVMS, RiscOS, etc.

    PWSH_ESCAPE: Final[str] = "`"
    VMS_ESCAPE: Final[str] = "^"
    NON_POSIX_EXPAND: Final[str] = "%"

    # Pre-defined non-POSIX constants

    DEFAULT_ESCAPES: Final[str] = POSIX_ESCAPE
    DEFAULT_EXPANDS: Final[str] = POSIX_EXPAND + NON_POSIX_EXPAND

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

###############################################################################
