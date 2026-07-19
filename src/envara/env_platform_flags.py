###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# Enumeration containing flags to control Env.get_platform_stack(...)
###############################################################################

from enum import IntFlag

###############################################################################


class EnvPlatformFlags(IntFlag):
    NONE = 0
    """No flag set."""

    ADD_EMPTY = 1 << 0
    """Add an empty entry, which is relevant to any platform."""


###############################################################################
