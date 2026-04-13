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

    HARD = 1
    """Hard-quoted string (in POSIX, single-quoted)"""

    NORMAL = 2
    """Normally quoted string (in POSIX, double-quoted)"""

    DEFAULT = NORMAL
    """Default value"""


###############################################################################
