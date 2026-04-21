###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# String unquoting details
###############################################################################


class EnvCharsData:
    """
    Special characters to facilitate parsing strings containing environment-
    related insets
    """

    ###########################################################################

    def __eq__(self, other) -> bool:
        """
        Deep equality checker

        :param self: The object

        :param other: The object to compare to
        """

        return (
            (other.expand == self.expand)
            and (other.windup == self.windup)
            and (other.escape == self.escape)
            and (other.cutter == self.cutter)
            and (other.hard_quote == self.hard_quote)
            and (other.normal_quote == self.normal_quote)
            and (other.all_quotes == self.all_quotes)
        )

    ###########################################################################

    def __init__(
        self,
        expand: str | None = None,
        windup: str | None = None,
        escape: str | None = None,
        cutter: str | None = None,
        hard_quote: str | None = None,
        normal_quote: str | None = None,
    ):
        """
        Constructor

        :param self: The object

        :param expand: String that denotes the start of an environment
            variable token
        :type expand: str

        :param windup: Character or string that denotes the end of an
            environment variable token in non-POSIX OSes (normally, the
            same as expand, but sometimes, might differ, like for RiscOS)
        :type windup: str

        :param escape: Escape character or string
        :type escape: str

        :param cutter: Character or string denoting the end of data in a
            string (a line comment start
        :type cutter: str

        :param hard_quote: Character for a literal string start and end
            that requires to avoid unescaping and expansion of the
            environment variables
        :type hard_quote: str

        :param normal_quote: Character for a normal string start and end
            that allows unescaping and expansion of the environment variables
        :type normal_quote: str
        """

        self.expand: str = expand or ""
        self.expand_len: int = len(self.expand)

        self.windup: str = windup or ""
        self.windup_len: int = len(self.windup)

        self.escape: str = escape or ""
        self.escape_len: int = len(self.escape)

        self.cutter: str = cutter or ""
        self.cutter_len: int = len(self.cutter)

        self.hard_quote: str = hard_quote or ""
        self.hard_quote_len: int = 1 if self.hard_quote else 0

        self.normal_quote: str = normal_quote
        self.normal_quote_len: int = 1 if self.normal_quote else 0

        self.all_quotes: str = self.hard_quote + self.normal_quote
        self.all_quotes_len: int = len(self.all_quotes)

    ###########################################################################

    def copy_with(
        self,
        expand: str | None = None,
        windup: str | None = None,
        escape: str | None = None,
        cutter: str | None = None,
        hard_quote: str | None = None,
        normal_quote: str | None = None,
    ):
        """
        Copy all properties to a new object replacing certain properties. See
        __init__ for the details on arguments

        :return: The destination object (to)
        :rtype: EnvCharsData
        """

        return EnvCharsData(
            expand=(expand if expand is not None else self.expand),
            windup=(windup if windup is not None else self.windup),
            escape=(escape if escape is not None else self.escape),
            cutter=(cutter if cutter is not None else self.cutter),
            hard_quote=(hard_quote if hard_quote is not None else self.hard_quote),
            normal_quote=(
                normal_quote if normal_quote is not None else self.normal_quote
            ),
        )


###############################################################################
