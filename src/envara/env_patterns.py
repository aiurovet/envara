###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# A class to expand environment variables, user info (~), arguments from a
# list and escaped characters (\t, \n, etc.) in a string. As well as remove
# line comments if needed
#
# Additionally, accepts bit flags to control what and hopw to expand
#
# This class also allows to avoid unnecessary dependency: easy to implement.
###############################################################################

import re
from typing import Final
from env import Env

###############################################################################


class EnvPatterns:
    """
    Static helper class to define 
    """

    ###########################################################################

    DOTENV: Final[Env] = Env(
        escapes="\\",
        expands="$%",
        cutters=["#"],
        pat_var="([\\\\]*)\\$({?)([A-Za-z_][A-Za-z_\\d]*)(}?)",
        pat_arg="([\\\\]*)\\$({?)([\\d]+)(}?)",
    )

    ###########################################################################

    POSIX: Final[Env] = Env(
        escapes="\\",
        expands="$",
        stoppers=["#"],
        pat_var="([\\\\]*)\\$({?)([A-Za-z_][A-Za-z_\\d]*)(}?)",
        pat_arg="([\\\\]*)\\$({?)([\\d]+)(}?)",
    )


###############################################################################
