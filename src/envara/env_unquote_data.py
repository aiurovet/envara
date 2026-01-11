###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# String unquoting details
###############################################################################

from dataclasses import dataclass
from typing import ClassVar

from env_quote_type import EnvQuoteType

###############################################################################


@dataclass
class EnvUnquoteData:
    """
    Details of what was found in a string while removing quotes as well as
    that string and the result of its unquoting
    """

    # Pre-defined POSIX constants

    POSIX_ESCAPE: ClassVar[str] = "\\"
    POSIX_EXPAND: ClassVar[str] = "$"

    # Pre-defined non-POSIX constants as used in .env files under numerous
    # other OSes: Windows, OpenVMS, RiscOS, etc.

    NON_POSIX_ESCAPE: ClassVar[str] = "\\"
    NON_POSIX_EXPAND: ClassVar[str] = "%"

    # Pre-defined non-POSIX constants

    DEFAULT_ESCAPES: ClassVar[str] = POSIX_ESCAPE
    DEFAULT_EXPANDS: ClassVar[str] = POSIX_EXPAND + NON_POSIX_EXPAND

    # First active escape character found while analyzing a string

    escape: str = None

    # First active expand character found while analyzing a string

    expand: str = None

    # The string that was analyzed

    input: str = None

    # Type of enclosing quotes found while analyzing a string

    quote_type: EnvQuoteType = EnvQuoteType.NONE

    # input after it was unquoted or further processed: e.g., unescaped

    result: str = None

###############################################################################
