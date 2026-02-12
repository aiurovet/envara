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

    # Related to UNIX: Linux, BSD, macOS, Cygwin, MSYS, etc.
    # Dir sep: '/'
    # Escape: '\'
    # Env vars: $VAR, $#VAR, ${VAR}, ${VAR:-${VAR2+${VAR3...}}}, ${#VAR}
    # Args: $1, ${1}, ${1:-${2+${3...}}}, $#
    # Substitute commands: $(...), `...`
    POSIX = 1

    # Windows, ReactOS, OS/2 or similar
    # Dir sep: '\'
    # Escape: '^'
    # Env vars: %VAR%, %VAR:~2:3%, %1, %~dpnx1
    # Args: %1, %~dpnx1
    WINDOWS = 2

    # Related to OpenVMS or similar
    # Dir sep: ':'
    # Escape: same as WINDOWS
    # Env vars: nothing, just the name of a variable defined earlier
    VMS = 3

    # Related to Risc OS
    # Dir sep: '.'
    # Escape: same as WINDOWS
    # Env vars: same as WINDOWS
    # Args: same as WINDOWS
    RISCOS = 4


###############################################################################
