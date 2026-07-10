###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# String unquoting details
###############################################################################


import re
from typing import ClassVar


class EnvCharsData:
    """
    Special characters to facilitate parsing strings containing environment-
    related insets, as well as a regular expression to facilitate splitting
    a string representing an OS-specific command into executable and arguments
    """

    DEFAULT_CMD_OPS: ClassVar[str] = " "
    """Default command-splitting operators"""

    DIGITS_ONLY_RE: ClassVar[re.Pattern[str]] = re.compile(r"^\d+$")
    """Regex to check whether the input contains digits only or not"""

    ###########################################################################

    def __eq__(self, other: object) -> bool:
        """
        Deep equality checker

        :param self: The object

        :param other: The object to compare to
        """

        if not isinstance(other, EnvCharsData):
            return False

        return (
            (other.is_posix == self.is_posix)
            and (other.is_windows == self.is_windows)
            and (other.expand == self.expand)
            and (other.windup == self.windup)
            and (other.escape == self.escape)
            and (other.cutter == self.cutter)
            and (other.hard_quote == self.hard_quote)
            and (other.normal_quote == self.normal_quote)
            and (other.all_quotes == self.all_quotes)
            and (other.cmd_ops == self.cmd_ops)
        )

    ###########################################################################

    def __init__(
        self,
        is_posix: bool | None = False,
        is_windows: bool | None = False,
        expand: str | None = None,
        windup: str | None = None,
        escape: str | None = None,
        cutter: str | None = None,
        hard_quote: str | None = None,
        normal_quote: str | None = None,
        cmd_ops: str | None = None,
    ):
        """
        Constructor

        :param self: The object

        :param is_posix: True if need to expand environment variables and
            command-line arguments in POSIX (more precisely, bash) style
        :type is_posix: bool | None

        :param is_windows: True if need to expand environment variables and
            command-line arguments in Windows (more precisely, DOS batch)
            style
        :type is_windows: bool | None

        :param expand: String that denotes the start of an environment
            variable token
        :type expand: str | None

        :param windup: Character or string that denotes the end of an
            environment variable token in non-POSIX OSes (normally, the
            same as expand, but in theory, might differ)
        :type windup: str | None

        :param escape: Escape character or string
        :type escape: str | None

        :param cutter: Character or string denoting the end of data in a
            string (a line comment start
        :type cutter: str | None

        :param hard_quote: Character for a literal string start and end
            that requires to avoid unescaping and expansion of the
            environment variables
        :type hard_quote: str | None

        :param normal_quote: Character for a normal string start and end
            that allows unescaping and expansion of the environment variables
        :type normal_quote: str | None

        :param normal_quote: Character for a normal string start and end
            that allows unescaping and expansion of the environment variables
        :type normal_quote: str | None

        :param cmd_ops: Command operators like pipe, angles, parentheses, etc.
        :type cmd_ops: str | None
        """

        self.expand: str = expand or ""
        self.expand_len: int = len(self.expand)

        self.is_posix: bool = True if is_posix else False
        self.is_windows: bool = True if is_windows else False

        self.windup: str = windup or ""
        self.windup_len: int = len(self.windup)

        self.escape: str = escape or ""
        self.escape_len: int = len(self.escape)

        self.cutter: str = cutter or ""
        self.cutter_len: int = len(self.cutter)

        self.hard_quote: str = hard_quote or ""
        self.hard_quote_len: int = 1 if self.hard_quote else 0

        self.normal_quote: str = normal_quote or ""
        self.normal_quote_len: int = 1 if self.normal_quote else 0

        self.all_quotes: str = self.hard_quote + self.normal_quote
        self.all_quotes_len: int = len(self.all_quotes)

        self.cmd_ops: str = cmd_ops or EnvCharsData.DEFAULT_CMD_OPS

        pat_str = "|".join([f"{re.escape(c)}+" for c in self.cmd_ops])

        # The from-character is escaped already
        pat_str = pat_str.replace(EnvCharsData.DEFAULT_CMD_OPS, r"s")

        self.cmd_ops_re: re.Pattern[str] = re.compile(rf"({pat_str})")

    ###########################################################################

    def copy_with(
        self,
        is_posix: bool | None = None,
        is_windows: bool | None = None,
        expand: str | None = None,
        windup: str | None = None,
        escape: str | None = None,
        cutter: str | None = None,
        hard_quote: str | None = None,
        normal_quote: str | None = None,
        cmd_ops: str | None = None,
    ):
        """
        Copy all properties to a new object replacing certain properties. See
        __init__ for the details on arguments

        :return: The destination object (to)
        :rtype: EnvCharsData
        """

        return EnvCharsData(
            is_posix=(is_posix if is_posix is not None else self.is_posix),
            is_windows=(is_windows if is_windows is not None else self.is_windows),
            expand=(expand if expand is not None else self.expand),
            windup=(windup if windup is not None else self.windup),
            escape=(escape if escape is not None else self.escape),
            cutter=(cutter if cutter is not None else self.cutter),
            hard_quote=(hard_quote if hard_quote is not None else self.hard_quote),
            normal_quote=(
                normal_quote if normal_quote is not None else self.normal_quote
            ),
            cmd_ops=(cmd_ops if cmd_ops is not None else self.cmd_ops),
        )

    ###########################################################################

    def split_glued(self, input: str | None = None) -> list[str]:
        """
        Splits input string ignoring any possible injected environment variable,
        sub-command, or quote. Used in Env.split() to split each argument
        after splitting the whole comand by valid whitespaces

        :param input: String to split
        :type input: str | None
        """
        if not input:
            return []

        fully_split = [x for x in self.cmd_ops_re.split(input) if x]

        prev_is_ampers = False
        prev_is_digits = False
        prev_is_redir = False

        result: list[str] = []
        last_no = -1

        for x in fully_split:
            curr_is_ampers = True if x == "&" else False
            curr_is_digits = EnvCharsData.DIGITS_ONLY_RE.search(x) is not None
            curr_is_redir = True if x in "<>" else False

            can_glue = (
                (prev_is_digits and curr_is_redir)
                or (prev_is_redir and curr_is_ampers)
                or (prev_is_ampers and curr_is_digits)
            )

            if can_glue:
                result[last_no] += x
            else:
                result.append(x)
                last_no += 1

            prev_is_ampers = curr_is_ampers
            prev_is_digits = curr_is_digits
            prev_is_redir = curr_is_redir

        return result


###############################################################################
