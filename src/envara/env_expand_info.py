###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# A supplementary class for Env
###############################################################################


import re
from typing import Final


###############################################################################


class EnvExpandInfo:
    """
    Rules for expansion of environment variables, arguments and special
    characters in a given string
    """

    # Special characters when they follow an odd number of ESCAPEs
    SPECIAL: Final[dict[str, str]] = {
        "a": "\a", "b": "\b", "f": "\f", "n": "\n",
        "r": "\r", "t": "\t", "v": "\v"
    }

    def __init__(
        self,
        expand: str = None,
        escape: str = None,
        pat_esc: str | re.Pattern = None,
        pat_var: str | re.Pattern = None,
        pat_arg: str | re.Pattern = None,
        flags: int = re.DOTALL | re.UNICODE
    ):
        """
        Constructor
        
        :param self: The object
        :param expand: A character the expands start with: "$" or "%"
        :type expand: str
        :param escape: A character used for escaped chars: "\\", "`", "^"
        :type escape: str
        :param pat_esc: A pattern to detect escaped chars: "\\n", "\\x41", ...
        :type pat_esc: str | re.Pattern
        :param pat_var: A pattern to detect environment variables' expansion
        :type pat_var: str | re.Pattern
        :param pat_arg: A pattern to detect CLI arguments' expansion
        :type pat_arg: str | re.Pattern
        """

        # Character indicating the beginning of an env var or arg no
        self.ESCAPE = escape

        # Character used as a prefix for special characters
        self.EXPAND = expand

        # Regular expression to find command-line arguments
        if isinstance(pat_arg, re.Pattern):
            self.RE_ARG = pat_arg
        else:
            self.RE_ARG = re.compile(pat_arg, flags)

        # Regular expression to find escaped characters
        if isinstance(pat_esc, re.Pattern):
            self.RE_ESC = pat_esc
        else:
            self.RE_ESC = re.compile(pat_esc, flags)

        # Regular expression to find environment variables
        if isinstance(pat_var, re.Pattern):
            self.RE_VAR = pat_var
        else:
            self.RE_VAR = re.compile(pat_var, flags)


###############################################################################
