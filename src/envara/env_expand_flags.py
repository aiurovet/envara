###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# Enumeration containing flags to control behaviour of Env.expand(...)
###############################################################################

from enum import IntFlag

###############################################################################


class EnvExpandFlags(IntFlag):
    NONE = 0
    """No flag set"""

    ALLOW_SHELL = 1 << 0
    """Execute raw shell commands like $(...) or `...` - expand_posix() only"""

    ALLOW_SUBPROC = 1 << 1
    """Parse shell commands like $(...) or `...` and execute - expand_posix() only"""

    REMOVE_LINE_COMMENT = 1 << 2
    """Remove hash "#" (outside the quotes if found) and everything beyond that"""

    REMOVE_QUOTES = 1 << 3
    """Remove leading and trailing quote, don't expand single-quoted str: "..." """

    SKIP_ENV_VARS = 1 << 4
    """Do not expand environment variables"""

    SKIP_SINGLE_QUOTED = 1 << 5
    """If a string is embraced in apostrophes, don't expand it"""

    UNESCAPE = 1 << 6
    """Expand escaped characters, this includes characters represented by
    their hexadecimal or unicode sequence (depends on NATIVE_ESCAPE flag)"""

    DEFAULT = ALLOW_SHELL | REMOVE_QUOTES | SKIP_SINGLE_QUOTED | UNESCAPE
    """Default set of flags"""


###############################################################################
