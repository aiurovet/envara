###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# Enumeration containing information about what kind of quotes were removed
# in Env.unquote(...) or should be set in Env.quote(...)
###############################################################################

from enum import IntEnum

###############################################################################


class EnvQuoteType(IntEnum):
    NONE = 0
    """String with no leading quote"""

    SINGLE = 1
    """Single-quoted string"""

    DOUBLE = 2
    """Double-quoted string"""


###############################################################################
