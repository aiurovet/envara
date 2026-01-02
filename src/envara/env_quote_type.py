###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# Enumeration containing information about what kind of quotes were removed
# in Env.unquote(...) or should be set in Env.quote(...)
###############################################################################

from enum import IntEnum

###############################################################################


class EnvQuoteType(IntEnum):
    # String with no leading quote
    NONE = 0

    # Single-quoted string
    SINGLE = 1

    # Double-quoted string
    DOUBLE = 2


###############################################################################
