###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# String unquoting details
###############################################################################

import re
from typing import ClassVar

from env_quote_type import EnvQuoteType

###############################################################################

#import re
def test():
    input = "\\\\$HOME"
    esc = r'\\'

    regex = re.compile(
        f"(^({esc}{esc})*|[^{esc}]({esc}{esc})*)\\$({{?)([A-Za-z_][A-Za-z_\\d]*)(}}?)",
        re.UNICODE
    )

    def parser(m: re.Match) -> str:
        g = m.groups()

        g1 = "None" if g[0] is None else f"\"{g[0]}\""
        g2 = "None" if g[1] is None else f"\"{g[1]}\""
        g3 = "None" if g[2] is None else f"\"{g[2]}\""
        g4 = "None" if g[3] is None else f"\"{g[3]}\""
        g5 = "None" if g[4] is None else f"\"{g[4]}\""
        g6 = "None" if g[5] is None else f"\"{g[5]}\""

        #print(f"1: {g1}, 2: {g2}, 3: {g3}, 4: {g4}, 5: {g5}, 6: {g6}")
        print(f"1: {g1}, 2: {g2}, 3: {g3}, 4: {g4}, 5: {g5}, 6: {g6}")

        return ""

    _ = regex.sub(parser, input)


###############################################################################

def get_escape_solver(
    escape: str,
) -> str:
    """
    Create a string that allows to skip the even number of escapes and
    ignore the following pattern if there is one more escape after
    
    :param escape: Plain escape character
    :type escape: str
    :return: Composed string to become a prefix in a pattern
    :rtype: str
    """
    esc = re.escape(escape)
    return f"(^({esc}{esc})*|[^{esc}]({esc}{esc})*)"


###############################################################################

def create_env_pattern(
    escape: str,
    expand: str,
    braces: str,
    fodder: str,
    is_symmetric: bool = False
) -> re.Pattern:
    """
    Create a string that allows to skip the even number of escapes and
    ignore the following pattern if there is one more escape after
    
    :param escape: Plain escape character
    :type escape: str
    :param expand: Plain expand character
    :type expand: str
    :param braces: Two enclosing braces or empty string
    :type braces: str
    :param fodder: The actual pattern string beyond the expand character
    :type fodder: str
    :param is_symmetric: True = surround fodder with expanders from both sides
    :type is_symmetric: bool
    :return: Compiled regular expression
    :rtype: re.Pattern
    """

    esc = re.escape(escape)
    exp = re.escape(expand)

    exp_grp = f"({exp})"

    pat: str = f"(^({esc}{esc})*|[^{esc}]({esc}{esc})*)" + \
        f"{exp_grp}{fodder}{exp_grp}" if is_symmetric else f"{exp}{fodder}"
    
    return re.compile(pat, EnvParseInfo.RE_FLAGS)

###############################################################################


class EnvParseInfo:
    """
    Details of what was found in a string while removing quotes as well as
    that string and the result of its unquoting
    """

    # Pre-defined constants

    NO_BRACES: ClassVar[str] = ""

    POSIX_BRACES: ClassVar[str] = "{}"
    POSIX_ESCAPE: ClassVar[str] = "\\"
    POSIX_EXPAND: ClassVar[str] = "$"

    PWSH_ESCAPE: ClassVar[str] = "`"
    PWSH_EXPAND: ClassVar[str] = POSIX_EXPAND

    WINDOWS_ESCAPE: ClassVar[str] = "^"
    WINDOWS_EXPAND: ClassVar[str] = "%"

    RE_FLAGS: ClassVar[int] = re.UNICODE
    RE_AL_NUM: ClassVar[str] = r"([A-Za-z_][A-Za-z_\d]*)"
    RE_MINIMAL: ClassVar[str] = r"([^=:]+)"
    RE_NUMBER: ClassVar[str] = r"([\d]+)"

    # Helps to find env var parttern based on expand and escape

    ARG_PATTERNS: ClassVar[dict[str, re.Pattern]] = {
        POSIX_EXPAND + POSIX_ESCAPE: create_env_pattern(
            POSIX_ESCAPE, POSIX_EXPAND, POSIX_BRACES, RE_NUMBER
        ),
        PWSH_EXPAND + PWSH_ESCAPE: create_env_pattern(
            PWSH_ESCAPE, PWSH_EXPAND, POSIX_BRACES, RE_NUMBER
        ),
        WINDOWS_EXPAND + POSIX_ESCAPE: create_env_pattern(
            POSIX_ESCAPE, WINDOWS_EXPAND, NO_BRACES, RE_NUMBER
        ),
        WINDOWS_EXPAND + WINDOWS_ESCAPE: create_env_pattern(
            WINDOWS_ESCAPE, WINDOWS_EXPAND, NO_BRACES, RE_NUMBER
        )
    }

    # Helps to find env var parttern based on expand and escape

    VAR_PATTERNS: ClassVar[dict[str, re.Pattern]] = {
        POSIX_EXPAND + POSIX_ESCAPE: create_env_pattern(
            POSIX_ESCAPE, POSIX_EXPAND, POSIX_BRACES, RE_AL_NUM
        ),
        PWSH_EXPAND + PWSH_ESCAPE: create_env_pattern(
            PWSH_ESCAPE, PWSH_EXPAND, POSIX_BRACES, RE_AL_NUM
        ),
        WINDOWS_EXPAND + POSIX_ESCAPE: create_env_pattern(
            POSIX_ESCAPE, WINDOWS_EXPAND, NO_BRACES, RE_MINIMAL,
            is_symmetric=True
        ),
        WINDOWS_EXPAND + WINDOWS_ESCAPE: create_env_pattern(
            WINDOWS_ESCAPE, WINDOWS_EXPAND, NO_BRACES, RE_MINIMAL,
            is_symmetric=True
        )
    }

    ###########################################################################

    def __init__(
        self,
        input: str | None = None,
        result: str | None = None,
        escape: str | None = None,
        expand: str | None = None,
        quote_type: EnvQuoteType = EnvQuoteType.NONE
    ):
        """
        Constructor
        
        :param self: The object
        :param input: String being unquoted
        :type input: str
        :param result: Result of unquoting
        :type result: str
        :param escape: First active escape character encountered
                       (e.g., "\\\\", "`", "^")
        :type escape: str
        :param expand: First active expand character encountered
                       (e.g., "$", "%", "<")
        :type expand: str
        :param quote_type: Type of enclosing quotes found
        :type quote_type: EnvQuoteType
        """

        self.escape: str = escape
        self.expand: str = expand
        self.input: str = input
        self.result: str = result

        self.quote_type: EnvQuoteType = quote_type

        # Initialize patterns based on known data
    
        self.arg_pattern, self.var_pattern = EnvParseInfo.find_patterns(
            expand=self.expand,
            escape=self.escape,
        )

    ###########################################################################

    @staticmethod
    def find_patterns(
        escape: str = None,
        expand: str = None,
    ) -> tuple[re.Pattern, re.Pattern]:
        """
        Find pattern for environment variables' and arguments' placeholders
        
        :param patterns: collection of expand-escape => regex mappings
        :type patterns: dict[str, re.Pattern]
        :param expand: Expand character used
        :type expand: str
        :param escape: Escape character used
        :type escape: str
        :return: Regex found in the map of patterns by a given key
        :rtype: re.Pattern
        """
        # Coalesce escape if not passed

        if (escape is None):
            escape = EnvParseInfo.POSIX_ESCAPE

        # Coalesce expand if not passed

        if (expand is None):
            expand = EnvParseInfo.POSIX_EXPAND

        # If expand and escape form a valid key to the set of patterns,
        # return the found pattern. Otherwise, None

        key: str = f"{escape}{expand}"

        return (
            EnvParseInfo.ARG_PATTERNS.get(key),
            EnvParseInfo.VAR_PATTERNS.get(key)
        )


###############################################################################
