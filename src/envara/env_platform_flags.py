###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# Enumeration containing flags to control Env.get_platform_stack(...)
###############################################################################

from enum import IntFlag

###############################################################################


class EnvPlatformFlags(IntFlag):
    # No flag set
    NONE = 0

    # Add empty: relevant to any platform
    ADD_EMPTY = 1 << 0

    # Add maximum platforms (compatibility with README/tests)
    ADD_MAX = 1 << 1

    # Default set of platforms
    DEFAULT = ADD_EMPTY


###############################################################################
