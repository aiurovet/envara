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

    SKIP_HARD_QUOTED = 1 << 4
    """If a string is embraced in hard quotes, don't expand it (literal string)"""

    STRIP_COMMENT = 1 << 5
    """Remove hash "#" (outside the quotes if found) and everything beyond that"""

    STRIP_SPACES = 1 << 6
    """If a string has whitespace(s) around, remove those"""

    UNESCAPE = 1 << 7
    """Expand escaped characters, this includes characters represented by
    their hexadecimal or unicode sequence (depends on NATIVE_ESCAPE flag)"""

    UNQUOTE = 1 << 8
    """Remove leading and trailing quote, don't expand single-quoted str: "..." """

    DEFAULT = ALLOW_SHELL | SKIP_HARD_QUOTED | STRIP_SPACES | UNESCAPE | UNQUOTE
    """Default set of flags"""

    DEFAULT_SPLIT = DEFAULT | STRIP_COMMENT
    """Default set of flags for Env.split()"""


###############################################################################
