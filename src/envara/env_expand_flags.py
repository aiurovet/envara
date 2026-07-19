###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# Enumeration containing flags to control the behaviour of Env.expand(...)
###############################################################################

from enum import IntFlag

###############################################################################


class EnvExpandFlags(IntFlag):
    NONE = 0
    """No flag set."""

    ALLOW_SHELL = 1 << 0
    """Execute raw shell commands like `$(...)` or `` `...` `` — ``expand_posix()`` only."""

    ALLOW_SUBPROC = 1 << 1
    """Parse and execute shell commands like `$(...)` or `` `...` `` — ``expand_posix()`` only."""

    SKIP_HARD_QUOTED = 1 << 2
    """If a string is enclosed in hard quotes, do not expand it (literal string)."""

    STRIP_COMMENT = 1 << 3
    """Remove `#` and everything after it (outside quotes, if found)."""

    STRIP_SPACES = 1 << 4
    """If a string has leading or trailing whitespace, remove it."""

    UNESCAPE = 1 << 5
    """Expand escaped characters, including characters represented by
    their hexadecimal or Unicode sequence (depends on `NATIVE_ESCAPE` flag)."""

    UNQUOTE = 1 << 6
    """Remove leading and trailing quotes; do not expand single-quoted strings (`'...'`)."""

    DEFAULT = ALLOW_SHELL | SKIP_HARD_QUOTED | STRIP_SPACES | UNESCAPE | UNQUOTE
    """Default set of flags."""

    DEFAULT_SPLIT = DEFAULT | STRIP_COMMENT
    """Default set of flags for ``Env.split()``."""


###############################################################################
