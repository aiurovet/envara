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

    POSIX_EXP_CHR: ClassVar[str] = "$"
    POSIX_ESC_CHR: ClassVar[str] = "\\"

    PWSH_EXP_CHR: ClassVar[str] = POSIX_EXP_CHR
    PWSH_ESC_CHR: ClassVar[str] = "`"

    WINDOWS_EXP_CHR: ClassVar[str] = "%"
    WINDOWS_ESC_CHR: ClassVar[str] = "^"

    ###########################################################################

    def __init__(
        self,
        input: str | None = None,
        result: str | None = None,
        exp_chr: str | None = None,
        esc_chr: str | None = None,
        quote_type: EnvQuoteType = EnvQuoteType.NONE
    ):
        """
        Constructor
        
        :param self: The object
        :param input: String being unquoted
        :type input: str
        :param result: Result of unquoting
        :type result: str
        :param exp_chr: First active expand character encountered
                        (e.g., "$", "%", "<")
        :type exp_chr: str
        :param esc_chr: First active escape character encountered
                        (e.g., "\\\\", "`", "^")
        :type esc_chr: str
        :param quote_type: Type of enclosing quotes found
        :type quote_type: EnvQuoteType
        """

        self.exp_chr: str = exp_chr
        self.esc_chr: str = esc_chr
        self.input: str = input
        self.quote_type: EnvQuoteType = quote_type
        self.result: str = result

###############################################################################
