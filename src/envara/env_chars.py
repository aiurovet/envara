###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# String unquoting details
###############################################################################

from typing import ClassVar

from envara.env_chars_data import EnvCharsData
import os

###############################################################################


class EnvChars:
    """
    Special characters and OS-indicative flags to facilitate parsing strings
    containing environment-related tokens
    """

    IS_POSIX: ClassVar[bool] = os.sep == "/"
    """True if the app is running under Linux, UNIX, BSD, macOS or smimilar"""

    IS_VMS: ClassVar[bool] = os.sep == ":"
    """True if the app is running under OpenVMS or similar"""

    IS_WINDOWS: ClassVar[bool] = os.sep == "\\"
    """True if the app is running under Windows or OS/2"""

    POSIX: ClassVar[EnvCharsData] = EnvCharsData(
        is_posix=True,
        is_windows=False,
        expand="$",
        windup="",
        escape="\\",
        cutter="#",
        hard_quote="'",
        normal_quote='"',
    )
    """POSIX-specific set of environment-related characters"""

    POSIX_WINDOWS: ClassVar[EnvCharsData] = POSIX.copy_with(escape="^")
    """POSIX-specific set of environment-related characters with Windows-style escape to allow POSIX-like expansions on Windows"""

    VMS: ClassVar = EnvCharsData(
        is_posix=False,
        is_windows=False,
        expand="'",
        windup="'",
        escape="^",
        cutter="!",
        hard_quote="",
        normal_quote='"',
    )
    """OpenVMS-specific set of environment-related characters"""

    WINDOWS: ClassVar = EnvCharsData(
        is_posix=False,
        is_windows=True,
        expand="%",
        windup="%",
        escape="^",
        cutter="::",
        hard_quote="",
        normal_quote='"',
    )
    """Windows-specific set of environment-related characters"""

    Default: ClassVar[EnvCharsData] = (
        VMS if IS_VMS else WINDOWS if IS_WINDOWS else POSIX
    ).copy_with()
    """Default OS-specific set of environment-related characters"""

    Current: ClassVar[EnvCharsData] = Default.copy_with()
    """Current set of environment-related characters (POSIX or Default)"""

    ###########################################################################

    @staticmethod
    def init_default() -> EnvCharsData:
        """
        Clone the current OS-specific EnvCharsData and point `EnvChars.Default`
        to that, then return it too

        :return: EnvChars.Default pointing to a copy of the current OS-specific
            data
        :rtype: EnvCharsData
        """
        EnvChars.Default = (
            EnvChars.VMS if EnvChars.IS_VMS else (
                EnvChars.WINDOWS if EnvChars.IS_WINDOWS else EnvChars.POSIX
            )
        ).copy_with()

        return EnvChars.Default

    ###########################################################################

    @staticmethod
    def select(based_on: str | None = None) -> EnvCharsData:
        """
        Initialize Default if not set (backward-compatible), then set Current based
        on the comment the passed string starts with.

        :param based_on: String to check for platform cutter to determine platform
        :type based_on: str
        """

        if not based_on:
            EnvChars.Current = EnvChars.Default.copy_with()
        elif EnvChars.POSIX.cutter and based_on.startswith(EnvChars.POSIX.cutter):
            EnvChars.Current = EnvChars.POSIX.copy_with()
        elif EnvChars.VMS.cutter and based_on.startswith(EnvChars.VMS.cutter):
            EnvChars.Current = EnvChars.VMS.copy_with()
        elif EnvChars.WINDOWS.cutter and based_on.startswith(EnvChars.WINDOWS.cutter):
            EnvChars.Current = EnvChars.WINDOWS.copy_with()
        else:
            EnvChars.Current = EnvChars.Default.copy_with()

        return EnvChars.Current


###############################################################################
