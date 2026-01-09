###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# Enumeration for referring to system-specific EnvExpandInfo
###############################################################################

from enum import IntEnum

###############################################################################


class EnvExpandInfoType(IntEnum):
    # Choose between the rest depending on IS_WINDOWS, IS_VMS,then what comes
    # first in the input string: "$" or "%", then "`" or "^"
    SYSTEM = 0

    # Related to UNIX-like systems: Linux/BSD/macOS/UNIX/Cygwin/MSYS
    POSIX = 1

    # Related to PowerShell;
    POWSH = 2

    # Related to old MS-DOS batches:
    MSDOS = 3

    # Related to VMS-like OSe (primarily, OpenVMS):
    VMS = 4


###############################################################################
