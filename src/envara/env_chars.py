###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# String unquoting details
###############################################################################

from typing import ClassVar
import envara

###############################################################################


class EnvChars:
    """
    Special characters to facilitate parsing strings containing environment-
    related insets
    """

    # Pre-defined constant objects

    CURRENT: ClassVar = None
    """Current set of special characters (POSIX or DEFAULT)"""

    DEFAULT: ClassVar = None
    """Default OS-specific set of special characters"""

    POSIX: ClassVar = None
    """Default POSIX set of special characters"""

    RISCOS: ClassVar = None
    """Default RiscOS set of special characters"""

    VMS: ClassVar = None
    """Default OpenVMS set of special characters"""

    WINDOWS: ClassVar = None
    """Default Windows set of special characters"""

    __is_initial: ClassVar[bool] = True
    """Flag to initialize static objects of this class"""

    ###########################################################################

    def __eq__(self, other) -> bool: 
        """
        Deep equality checker

        :param self: The object

        :param other: The object to compare to
        """

        return (other.expand == self.expand)\
            and (other.windup == self.windup)\
            and (other.escape == self.escape)\
            and (other.cutter == self.cutter)\
            and (other.hard_quote == self.hard_quote)\
            and (other.normal_quote == self.normal_quote)\
            and (other.all_quotes == self.all_quotes)

    ###########################################################################

    def __init__(
        self,
        expand: str | None = None,
        windup: str | None = None,
        escape: str | None = None,
        cutter: str | None = None,
        hard_quote: str | None = None,
        normal_quote: str | None = None
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

        if (not EnvChars.DEFAULT) and EnvChars.__is_initial:
            EnvChars.__is_initial = False
            EnvChars.select()

        self.expand: str = expand or ""
        self.expand_len: str = len(self.expand)

        self.windup: str = windup or ""
        self.windup_len: str = len(self.windup)

        self.escape: str = escape or ""
        self.escape_len: str = len(self.escape)

        self.cutter: str = cutter or ""
        self.cutter_len: str = len(self.cutter)

        self.hard_quote: str = hard_quote or ""
        self.hard_quote_len: str = 1 if self.hard_quote else 0

        self.normal_quote: str = normal_quote
        self.normal_quote_len: str = 1 if self.normal_quote else 0

        self.all_quotes: str = self.hard_quote + self.normal_quote
        self.all_quotes_len: str = len(self.all_quotes)

    ###########################################################################

    def copy_to(self, to):
        """
        Copy all properties to another or new object

        :param self: The object (source)

        :param to: Destination object. If passed as None, the new one will be
            created, filled and returned
        :type input: EnvChars

        :return: The destination object (to)
        :rtype: EnvChars
        """

        if to:
            to.expand = self.expand
            to.expand_len = self.expand_len

            to.windup = self.windup
            to.windup_len = self.windup_len

            to.escape = self.escape
            to.escape_len = self.escape_len

            to.cutter = self.cutter
            to.cutter_len = self.cutter_len

            to.hard_quote = self.hard_quote
            to.hard_quote_len = self.hard_quote_len

            to.normal_quote = self.normal_quote
            to.normal_quote_len = self.normal_quote_len

            to.all_quotes = self.all_quotes
            to.all_quotes_len = self.all_quotes_len

            return to

        return EnvChars(
            expand=self.expand,
            windup=self.windup,
            escape=self.escape,
            cutter=self.cutter,
            hard_quote=self.hard_quote,
            normal_quote = self.normal_quote
        )

    ###########################################################################

    @staticmethod
    def select(based_on: str = None):
        """
        Initialize static properties if not done that yet, then set CURRENT
        
        :param is_posix: Set CURRENT to POSIX (True) or DEFAULT (False)
        :type is_posix: bool
        """

        # Initialize static properties if not done that yet

        if not EnvChars.DEFAULT:
            EnvChars.POSIX = EnvChars(
                expand="$",
                windup="",
                escape="\\",
                cutter="#",
                hard_quote="'",
                normal_quote='"'
            )
            EnvChars.RISCOS = EnvChars(
                expand="<",
                windup=">",
                escape="\\",
                cutter="|",
                hard_quote="",
                normal_quote='"'
            )
            EnvChars.VMS = EnvChars(
                expand="'",
                windup="'",
                escape="^",
                cutter="!",
                hard_quote="",
                normal_quote='"'
            )
            EnvChars.WINDOWS = EnvChars(
                expand="%",
                windup="%",
                escape="^",
                cutter="::",
                hard_quote="",
                normal_quote='"'
            )

        # Select the default chars based on the current OS

        if envara.Env.IS_RISCOS:
            EnvChars.DEFAULT = EnvChars.RISCOS.copy_to()
        elif envara.Env.IS_VMS:
            EnvChars.DEFAULT = EnvChars.VMS.copy_to()
        elif envara.Env.IS_WINDOWS:
            EnvChars.DEFAULT = EnvChars.WINDOWS.copy_to()
        else:
            EnvChars.DEFAULT = EnvChars.POSIX.copy_to()

        # Select the current chars based on the comments the passed string
        # starts with

        if based_on.startswith(EnvChars.RISCOS):
            EnvChars.CURRENT = EnvChars.RISCOS.copy_to()
        elif based_on.startswith(EnvChars.VMS):
            EnvChars.CURRENT = EnvChars.VMS.copy_to()
        elif based_on.startswith(EnvChars.WINDOWS):
            EnvChars.CURRENT = EnvChars.WINDOWS.copy_to()
        else:
            EnvChars.CURRENT = EnvChars.POSIX.copy_to()


###############################################################################