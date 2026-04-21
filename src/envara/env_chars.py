###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# String unquoting details
###############################################################################

from typing import ClassVar
#import envara
from env_chars_data import EnvCharsData
import os

###############################################################################


class EnvChars:
    """
    Special characters and OS-indicative flags to facilitate parsing strings
    containing environment-related tokens
    """

    IS_POSIX: ClassVar[bool] = os.sep == "/"
    """True if the app is running under Linux, UNIX, BSD, macOS or smimilar"""

    IS_RISCOS: ClassVar[bool] = os.sep == "."
    """True if the app is running under Risc OS"""

    IS_VMS: ClassVar[bool] = os.sep == ":"
    """True if the app is running under OpenVMS or similar"""

    IS_WINDOWS: ClassVar[bool] = os.sep == "\\"
    """True if the app is running under Windows or OS/2"""

    POSIX: ClassVar[EnvCharsData] = EnvCharsData(
        expand="$", windup="", escape="\\", cutter="#", hard_quote="'", normal_quote='"'
    )
    """POSIX-specific set of environment-related characters"""

    RISCOS: ClassVar = EnvCharsData(
        expand="<", windup=">", escape="\\", cutter="|", hard_quote="", normal_quote='"'
    )
    """RiscOS-specific set of environment-related characters"""

    VMS: ClassVar = EnvCharsData(
        expand="'", windup="'", escape="^", cutter="!", hard_quote="", normal_quote='"'
    )
    """OpenVMS-specific set of environment-related characters"""

    WINDOWS: ClassVar = EnvCharsData(
        expand="%", windup="%", escape="^", cutter="::", hard_quote="", normal_quote='"'
    )
    """Windows-specific set of environment-related characters"""

    DEFAULT: ClassVar[EnvCharsData] = \
        RISCOS.copy_with() if IS_RISCOS\
        else VMS.copy_with() if IS_VMS\
        else WINDOWS.copy_with() if IS_WINDOWS\
        else POSIX.copy_with()
    """Default OS-specific set of environment-related characters"""

    CURRENT: ClassVar[EnvCharsData] = DEFAULT.copy_with()
    """Current set of environment-related characters (POSIX or DEFAULT)"""

    ###########################################################################

    @staticmethod
    def init_default() -> EnvCharsData:
        if EnvChars.IS_RISCOS:
            EnvChars.DEFAULT = EnvChars.RISCOS.copy_with()
        elif EnvChars.IS_VMS:
            EnvChars.DEFAULT = EnvChars.VMS.copy_with()
        elif EnvChars.IS_WINDOWS:
            EnvChars.DEFAULT = EnvChars.WINDOWS.copy_with()
        else:
            EnvChars.DEFAULT = EnvChars.POSIX.copy_with()
    
        return EnvChars.DEFAULT

    ###########################################################################

    @staticmethod
    def select(based_on: str = None) -> EnvCharsData:
        """
        Initialize DEFAULT if not set (backward-compatible), then set CURRENT based
        on the comment the passed string starts with.

        :param based_on: String to check for platform cutter to determine platform
        :type based_on: str
        """

        if not EnvChars.DEFAULT:
            EnvChars.init_default()

        if not based_on:
            EnvChars.CURRENT = EnvChars.DEFAULT.copy_with()
        elif EnvChars.POSIX.cutter and based_on.startswith(EnvChars.POSIX.cutter):
            EnvChars.CURRENT = EnvChars.POSIX.copy_with()
        elif EnvChars.RISCOS.cutter and based_on.startswith(EnvChars.RISCOS.cutter):
            EnvChars.CURRENT = EnvChars.RISCOS.copy_with()
        elif EnvChars.VMS.cutter and based_on.startswith(EnvChars.VMS.cutter):
            EnvChars.CURRENT = EnvChars.VMS.copy_with()
        elif EnvChars.WINDOWS.cutter and based_on.startswith(EnvChars.WINDOWS.cutter):
            EnvChars.CURRENT = EnvChars.WINDOWS.copy_with()
        else:
            EnvChars.CURRENT = EnvChars.DEFAULT.copy_with()

        return EnvChars.CURRENT


###############################################################################
