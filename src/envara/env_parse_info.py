###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# String unquoting details
###############################################################################

from typing import ClassVar
from envara.env_quote_type import EnvQuoteType


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

    RISCOS_CUTTER_CHAR: ClassVar[str] = "|"
    RISCOS_EXPAND_CHAR: ClassVar[str] = "<"
    RISCOS_WINDUP_CHAR: ClassVar[str] = ">"
    RISCOS_ESCAPE_CHAR: ClassVar[str] = "\\"

    VMS_CUTTER_CHAR: ClassVar[str] = "!"
    VMS_EXPAND_CHAR: ClassVar[str] = "'"
    VMS_ESCAPE_CHAR: ClassVar[str] = "^"

    WINDOWS_CUTTER_CHAR: ClassVar[str] = ""
    WINDOWS_EXPAND_CHAR: ClassVar[str] = "%"
    WINDOWS_ESCAPE_CHAR: ClassVar[str] = "^"

    ###########################################################################

    def __init__(
        self,
        input: str | None = None,
        result: str | None = None,
        expand_char: str | None = None,
        windup_char: str | None = None,
        escape_char: str | None = None,
        cutter_char: str | None = None,
        quote_type: EnvQuoteType = EnvQuoteType.NONE,
    ):
        """
        Constructor

        :param self: The object

        :param input: String being unquoted
        :type input: str

        :param result: Result of unquoting
        :type result: str

        :param expand_char: First non-escaped and non-quoted expand character
            encountered: dollar, percent, angle bracket
        :type expand_char: str

        :param windup_char: Character that acts as the end of an environment
            variable token in non-POSIX OSes (normally, the same as
            expand_char, but sometimes, might differ, like for RiscOS)
        :type windup_char: str

        :param escape_char: First non-escaped and non-quoted character
            encountered: backslash, backtick, caret
        :type escape_char: str

        :param cutter_char: First non-escaped and non-quoted character
            recognised as the end of data in a string (like a line comment
            start): hash
        :type cutter_char: str

        :param quote_type: Type of enclosing quotes found
        :type quote_type: EnvQuoteType
        """

        self.expand_char: str = expand_char
        self.escape_char: str = escape_char
        self.cutter_char: str = cutter_char
        self.input: str = input
        self.quote_type: EnvQuoteType = quote_type
        self.result: str = result
        self.windup_char: str = windup_char

        if not self.windup_char:
            if self.expand_char == EnvParseInfo.RISCOS_EXPAND_CHAR:
                self.windup_char = EnvParseInfo.RISCOS_WINDUP_CHAR
            else:
                self.windup_char = self.expand_char

    ###########################################################################

    def copy_to(self, to):
        """
        Copy all properties to another object

        :param self: The object (source)

        :param to: Destination object
        :type input: EnvParseInfo

        :return: The destination object (to)
        :rtype: EnvParseInfo
        """

        if not to:
            return to

        to.expand_char = self.expand_char
        to.windup_char = self.windup_char
        to.escape_char = self.escape_char
        to.cutter_char = self.cutter_char
        to.input = self.input
        to.quote_type = self.quote_type
        to.result = self.result

        return to


###############################################################################
