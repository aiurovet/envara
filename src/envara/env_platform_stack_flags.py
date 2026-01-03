###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# Enumeration containing flags to control Env.get_platform_stack(...)
###############################################################################

from enum import IntFlag

###############################################################################


class EnvPlatformStackFlags(IntFlag):
    # No flag set
    NONE = 0

    # Add empty: relevant to any platform
    ADD_EMPTY = 1 << 0

    # Add Env.PLATFORM_ANY: relevant to any platform
    ADD_ANY = 1 << 1

    # Add current platform
    ADD_CURRENT = 1 << 2

    # Add maximum platforms possible
    ADD_MAX = ADD_EMPTY | ADD_ANY | ADD_CURRENT

    # Default set of platforms
    DEFAULT = ADD_MAX


###############################################################################
