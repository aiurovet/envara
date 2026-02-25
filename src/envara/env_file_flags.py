###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# Enumeration containing flags to control behaviour of EnvFile methods
###############################################################################

from enum import IntFlag

###############################################################################


class EnvFileFlags(IntFlag):
    NONE = 0
    """No flag set"""

    ADD_PLATFORMS = 1 << 0
    """Add platforms to be present in the filenames"""

    RESET_ACCUMULATED = 1 << 1
    """Drop internal accumulations from the previous runs"""


###############################################################################
