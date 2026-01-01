###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# Enumeration containing flags to control behaaviour of Env.expand(...)
###############################################################################

from enum import IntFlag

###############################################################################


class EnvExpandFlags(IntFlag):
    # No flag set
    NONE = 0

    # Expand escaped characters: \\ or `\`, \n or `n, \uNNNN or `uNNNN`, etc.
    # (depends on NATIVE_ESCAPE flag)
    DECODE_ESCAPED = (1<<0)

    # Remove hash '#' (outside the quotes if found) and everything beyond that
    REMOVE_LINE_COMMENT = (1<<2)

    # Remove leading and trailing quote, don't expand single-quoted str: '...'
    REMOVE_QUOTES = (1<<3)

    # If a string is embraced in apostrophes, don't expand it
    SKIP_SINGLE_QUOTED = (1<<4)

    # Default set of flags
    DEFAULT = (DECODE_ESCAPED | REMOVE_LINE_COMMENT | \
               REMOVE_QUOTES | SKIP_SINGLE_QUOTED)

###############################################################################
