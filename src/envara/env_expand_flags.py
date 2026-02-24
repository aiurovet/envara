###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# Enumeration containing flags to control behaviour of Env.expand(...)
###############################################################################

from enum import IntFlag

###############################################################################


class EnvExpandFlags(IntFlag):
    # No flag set
    NONE = 0

    # Execute raw shell commands like $(...) or `...` - expand_posix() only
    ALLOW_SHELL = 1 << 0

    # Parse shell commands like $(...) or `...` and execute - expand_posix() only
    ALLOW_SUBPROC = 1 << 1

    # Remove hash "#" (outside the quotes if found) and everything beyond that
    REMOVE_LINE_COMMENT = 1 << 2

    # Remove leading and trailing quote, don't expand single-quoted str: "..."
    REMOVE_QUOTES = 1 << 3

    # Do not expand environment variables
    SKIP_ENV_VARS = 1 << 4

    # If a string is embraced in apostrophes, don't expand it
    SKIP_SINGLE_QUOTED = 1 << 5

    # Expand escaped characters: \\ or `\`, \n or `n, \uNNNN or `uNNNN`, etc.
    # (depends on NATIVE_ESCAPE flag)
    UNESCAPE = 1 << 6

    # Default set of flags
    DEFAULT = ALLOW_SHELL | REMOVE_QUOTES | SKIP_SINGLE_QUOTED | UNESCAPE


###############################################################################
