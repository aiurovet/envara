###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# Enumeration containing flags to control behaviour of DotEnv methods
###############################################################################

from enum import IntFlag

###############################################################################


class DotEnvFileFlags(IntFlag):
    # No flag set
    NONE = 0

    # Drop internal accumulations from the previous runs
    RESET = 1 << 0

    # Do not load the default files
    SKIP_DEFAULT_FILES = 1 << 1

    # Do not prepend system-specfic files with a dot
    VISIBLE_FILES = 1 << 2

    # Default combination
    DEFAULT = NONE


###############################################################################
