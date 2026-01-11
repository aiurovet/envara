###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# Enumeration for referring to system-specific environments
###############################################################################

from enum import IntEnum

###############################################################################


class EnvType(IntEnum):
    # Failed to determine
    UNKNOWN = 0

    # Related to UNIX similar: Linux, BSD, macOS, Cygwin, MSYS, etc.
    # Dir sep: /
    # Escape: \
    # Env vars: $VAR, ${VAR}, $1, ${1}
    POSIX = 1

    # Windows, ReactOS, OS/2 or similar
    # Dir sep: \
    # Escape: use POSIX and escape dir sep
    # Env vars: use POSIX or %VAR%, %1
    WINDOWS = 2

    # Related to OpenVMS or similar
    # Dir sep: :
    # Escape: same as WINDOWS
    # Env vars: same as WINDOWS
    VMS = 3

    # Related to Risc OS
    # Dir sep: .
    # Escape: same as WINDOWS
    # Env vars: same as WINDOWS
    RISCOS = 4


###############################################################################
