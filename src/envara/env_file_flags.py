###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# Enumeration containing flags to control behaviour of EnvFile methods
###############################################################################

from enum import IntFlag

###############################################################################


class EnvFileFlags(IntFlag):
    # No flag set
    NONE = 0

    # Add platforms to be present in the filenames
    ADD_PLATFORMS = 1 << 0

    # Drop internal accumulations from the previous runs
    RESET = 1 << 1

    # Default combination
    DEFAULT = ADD_PLATFORMS


###############################################################################
