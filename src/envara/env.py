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

import os
import re
import string
import sys
from typing import Any, Final

from env_expand_flags import EnvExpandFlags
from env_expand_info import EnvExpandInfo
from env_expand_info_type import EnvExpandInfoType
from env_platform_stack_flags import EnvPlatformStackFlags
from env_quote_type import EnvQuoteType
from env_unquote_info import EnvUnquoteInfo

###############################################################################


class Env:
    """
    Class for string expansions
    """

    # Default escape character
    POSIX_ESCAPE: Final[str] = "\\"

    # Default expand character
    POSIX_EXPAND: Final[str] = "$"

    # True if the app is running under Linux, UNIX, BSD, macOS or smimilar
    IS_POSIX: Final[bool] = os.sep == "/"

    # True if the app is running under Windows or OS/2
    IS_WINDOWS: Final[bool] = os.sep == "\\"

    # True if the app is running under OpenVMS or similar
    IS_VMS: Final[bool] = os.sep == ":"

    # True if the app is running under Risc OS
    IS_RISCOS: Final[bool] = os.sep == "."

    # A text indicating any platform, but not empty
    PLATFORM_ANY: Final[str] = "any"

    # A text indicating a POSIX-compatible platform
    PLATFORM_POSIX: Final[str] = "posix"

    # A text indicating a Windows-compatible platform
    PLATFORM_WINDOWS: Final[str] = "windows"

    # A text indicating the running platform
    PLATFORM_THIS: Final[str] = sys.platform.lower()

    # Special characters when they follow an odd number of ESCAPEs
    SPECIAL: Final[dict[str, str]] = {
        "a": "\a", "b": "\b", "f": "\f", "n": "\n",
        "r": "\r", "t": "\t", "v": "\v"
    }

    # Expansion/unescaping info - MSDOS-style
    __msdos_info: EnvExpandInfo = EnvExpandInfo(
        expand="%",
        escape="^",
        pat_esc="([\\^]+)(x([\\dA-Fa-f]{2})|u([\\dA-Fa-f]{4})|.)",
        pat_var="([\\^]*)(%)([A-Za-z_][A-Za-z_\\d]*)(%)",
        pat_arg="([\\^]*)(%)([\\d]+)(%)",
    )

    # Expansion/unescaping info - POSIX-style
    __posix_info: EnvExpandInfo = EnvExpandInfo(
        expand="$",
        escape="\\",
        pat_esc="([\\\\]+)(x([\\dA-Fa-f]{2})|u([\\dA-Fa-f]{4})|.)",
        pat_var="([\\\\]*)\\$({?)([A-Za-z_][A-Za-z_\\d]*)(}?)",
        pat_arg="([\\\\]*)\\$({?)([\\d]+)(}?)",
    )

    __powsh_info: EnvExpandInfo = EnvExpandInfo(
        expand="$",
        escape="`",
        pat_esc="([`]+)(x([\\dA-Fa-f]{2})|u([\\dA-Fa-f]{4})|.)",
        pat_var="([`]*)\\$({?)([A-Za-z_][A-Za-z_\\d]*)(}?)",
        pat_arg="([`]*)\\$({?)([\\d]+)(}?)",
    )

    __vms_info: EnvExpandInfo = EnvExpandInfo(
        expand="'",
        escape="^",
        pat_esc="([\\^]+)(x([\\dA-Fa-f]{2})|u([\\dA-Fa-f]{4})|.)",
        pat_var="([\\^]*)(')([A-Za-z_][A-Za-z_\\d]*)(')",
        pat_arg="([\\^]*)(')([\\d]+)(')",
    )

    # Internal dictionary: regex => list-of-platform-names
    __platform_map: dict[str, list[str]] = {
        "": ["", PLATFORM_ANY, PLATFORM_POSIX], # the latter is checked
        "^aix": ["aix"],
        "android": ["linux", "android"],
        "^atheos": ["atheos"],
        "^beos|haiku": ["beos", "haiku"],
        "bsd": ["bsd"],
        "cygwin": ["cygwin"],
        "hp-ux": ["hp-ux"],
        "darwin|macos": ["bsd", "darwin", "macos"],
        "^ios|ipados": ["bsd", "ios"],
        "java": [PLATFORM_POSIX, PLATFORM_WINDOWS],  # only one will fit
        "^linux": ["linux"],
        "^os2": ["os2"],
        "^msys": ["msys"],
        "^riscos": ["riscos"],
        "sunos": ["sunos"],
        "unix": ["unix"],
        "vms": ["vms"],
        "^win": [PLATFORM_WINDOWS],
        ".+": [PLATFORM_THIS],
    }

    ###########################################################################

    @staticmethod
    def expand(
        input: str,
        args: list[str] | None = None,
        flags: EnvExpandFlags = EnvExpandFlags.DEFAULT,
    ) -> str:
        """
        Unquote the input if required, remove trailing line comment if
        required, expand the result with the arguments if required, expand
        the result with the environment variables' values. The method follows
        minimal POSIX conventions: $ABC and ${ABC}, as well as %ABC% on Windows

        :param input: Input string to expand
        :type input: str
        :param args: List of arguments to expand from $1, ...
        :type args: str
        :param flags: Flags controlling what/how to expand input
        :type flags: EnvExpandFlags
        :return: Expanded string
        :rtype: str
        """

        # For input as None or the empty string, return empty string

        if not input:
            return ""

        # Initialise

        result = (
            input.replace(f"{Env.ESCAPE}$", Env.HIDE_01)
            .replace(f'{Env.ESCAPE}"', Env.HIDE_02)
            .replace(Env.ESCAPE_ESCAPED, Env.HIDE_03)
        )

        # Simplify flags

        is_remove_line_comment: bool = flags & EnvExpandFlags.REMOVE_LINE_COMMENT
        is_remove_quotes: bool = flags & EnvExpandFlags.REMOVE_QUOTES
        is_skip_environ: bool = flags & EnvExpandFlags.SKIP_ENVIRON
        is_skip_single_quoted: bool = flags & EnvExpandFlags.SKIP_SINGLE_QUOTED
        is_unescape: bool = flags & EnvExpandFlags.UNESCAPE

        # Prepare for the unquoting and further unhiding

        quote_type: EnvQuoteType = EnvQuoteType.NONE
        unhide_escape = Env.ESCAPE

        # If the unquoting requested, do that treating a single-quoted input
        # as literal (no further expansion) if required

        if is_remove_quotes:
            result, quote_type = Env.unquote(result, unescape=False)

        # Remove line comment if required

        if (quote_type == EnvQuoteType.NONE) and is_remove_line_comment:
            result = Env.remove_line_comment(result)

        # If not a single-quoted string, try expanding user and vars

        if not is_skip_single_quoted or (quote_type != EnvQuoteType.SINGLE):

            # If the user indicator is found, expand the string

            if "~" in result:
                result = os.path.expanduser(result)

            # If the sought indicator found in the string, expand arguments
            # if the list of those passed, then expand the environment
            # variables if allowed

            if ("$" in result) or (Env.IS_WINDOWS and ("%" in result)):
                if args:
                    result = Env.expand_args(result, args)
                if not is_skip_environ:
                    result = os.path.expandvars(result)

            # If decoding escaped characters, shouldn't restore the escape

            if is_unescape:
                unhide_escape = ""
                result = Env.unescape(result)

        result = (
            result.replace(Env.HIDE_01, f"{unhide_escape}$")
            .replace(Env.HIDE_02, f'{unhide_escape}"')
            .replace(Env.HIDE_03, f"{unhide_escape}{Env.ESCAPE}")
        )

        # Return the final result

        return result

    ###########################################################################

    @staticmethod
    def expand_args(input: str, args: list[str] | None = None) -> str:
        """
        Expand references to an array of arguments by its indices

        :param input: String being expanded
        :type input: str
        :param args: List of arguments to refer to
        :type args: list[str]
        :return: Expanded string
        :rtype: str
        """

        # If input is None or empty, return empty string

        if not input:
            return ""

        # Get how many args and return input intact if no arg passed

        arg_cnt = len(args) if args else 0

        if arg_cnt <= 0:
            return input

        # Define regex match evaluator

        def matcher(match):
            idx_str = match.group(1) or match.group(2)

            if (not idx_str) and Env.IS_WINDOWS:
                idx_str = match.group(3)

                if not idx_str:
                    return match.group(0)

            idx_int = int(idx_str) - 1

            if (idx_int >= 0) and (idx_int < arg_cnt):
                return args[idx_int]

            return match.group(0)

        # Run the substitution

        return Env.RE_ARGS.sub(matcher, input)

    ###########################################################################

    @staticmethod
    def get_platform_stack(
        flags: EnvPlatformStackFlags = EnvPlatformStackFlags.DEFAULT,
        prefix: str | None = None,
        suffix: str | None = None,
    ) -> list[str]:
        """
        Get the stack (list) of platforms from more generic to more specific
        ones

        :param flags: Controls which items will be added to the stack
        :type flags: EnvPlatformStackFlags
        :param prefix: A string to prepend every platform name with
        :type prefix: str
        :param suffix: A string to append to every platform name
        :type suffix: str
        :return: A list of all relevant platforms with an optional decoration
        :rtype: list[str]
        """

        # Adjust parameters

        prefix: str = "" if (prefix is None) else prefix
        suffix: str = "" if (suffix is None) else suffix

        is_decorated: bool = True if (prefix or suffix) else False

        # Initialize the return value

        result: list[str] = []

        # Traverse the {pattern: list-of-relevant-platforms} dictionary and
        # append those where the pattern matches the running platform

        re_flags = re.IGNORECASE | re.UNICODE

        for pattern, platforms in Env.__platform_map.items():

            # If the platform doesn't match the running one, skip it

            if pattern:
                if not re.search(pattern, Env.PLATFORM_THIS, re_flags):
                    continue

            # Append every platform from the current list if eligible

            for platform in platforms:

                # Perform extra checks

                if not platform:
                    if (flags & EnvPlatformStackFlags.ADD_EMPTY) == 0:
                        continue
                elif platform == Env.PLATFORM_ANY:
                    if (flags & EnvPlatformStackFlags.ADD_ANY) == 0:
                        continue
                elif platform == Env.PLATFORM_THIS:
                    if (flags & EnvPlatformStackFlags.ADD_CURRENT) == 0:
                        continue
                elif platform == Env.PLATFORM_POSIX:
                    if not Env.IS_POSIX:
                        continue
                elif platform == Env.PLATFORM_WINDOWS:
                    if not Env.IS_WINDOWS:
                        continue

                # Decorate the platform name if needed
                # If the platform name is empty, and suffix starts with prefix
                # (like "." and ".env"), take suffix alone (i.e. merge)

                if is_decorated:
                    if ((not platform) and prefix and suffix and (
                        suffix[len(prefix) - 1] == prefix[0]
                    )):
                        platform = f"{prefix}{platform}{suffix[1:]}"
                    else:
                        platform = f"{prefix}{platform}{suffix}"

                # If the platform name was not added yet, add it

                if platform not in result:
                    result.append(platform)

        # Return the accumulated list

        return result

    ###########################################################################

    @staticmethod
    def quote(
        input: str,
        type: EnvQuoteType = EnvQuoteType.DOUBLE,
        escape: str = None
    ) -> str:
        """
        Enclose input in quotes. Neither leading, nor trailing whitespaces
        removed before checking the leading quotes. Use .strip() yourself
        before calling this method if needed.

        :param input: String being expanded
        :type input: str
        :param type: Type of quotes to enclose in
        :type type: EnvQuoteType
        :param escape: Escape character to use
        :type escape: str
        :return: Quoted string with possible quotes and escape characters from
                 the inside being escaped
        :rtype: str
        """

        # Initialise

        result = "" if (input is None) else input

        if (not escape):
            escape = EnvUnquoteInfo.DEFAULT_ESCAPES[0]

        # Define the quote being used

        if type == EnvQuoteType.SINGLE:
            quote = "'"
        elif type == EnvQuoteType.DOUBLE:
            quote = '"'
        else:
            quote = ""

        # If quote is empty, return the input itself

        if not quote:
            return result

        # If input is not empty, escape the escape character, then the
        # internal quote(s), then embrace the result in desired quotes
        # and return

        if result and (quote in result):
            if escape in result:
                result = result.replace(escape, f"{escape}{escape}")
            result = result.replace(quote, f"{escape}{quote}")

        return f"{quote}{result}{quote}"

    ###########################################################################

    @staticmethod
    def unescape(input: str, escape: str = None) -> str:
        """
        Unescape '\\t', '\\n', '\\u0022' etc.

        :param input: Input string to unescape escaped characters in
        :type input: str
        :param expand_info: How to expand (default: determine it)
        :type expand_info: EnvExpandInfo
        :return: Unescaped string
        :rtype: str
        """

        # If input is void, return empty string

        if not input:
            return ""

        # If escape character is not known yet, use the default one, and
        # if input does not contain the default escape char, then finish

        if (not escape):
            escape = EnvUnquoteInfo.DEFAULT_ESCAPES[0]
            if escape not in input:
                return input

        # Loop through the input and accumulate valid characters in chr_lst

        chr_lst: list[str] = []
        cur_pos: int = -1
        esc_pos: int = -1
        is_escaped: bool = False

        # Start and end of a substring to accumulate for the code-to-string
        # conversion

        acc_beg_pos: int = -1
        acc_end_pos: int = -1

        for cur_chr in input:
            cur_pos = cur_pos + 1

            if (cur_pos >= acc_beg_pos) and (cur_pos < acc_end_pos):
                if (cur_chr not in string.hexdigits):
                    Env.__fail_unescape(input, esc_pos, cur_pos)
                continue

            if (cur_pos == acc_end_pos):
                chr_lst.append(chr(int(input[acc_beg_pos:acc_end_pos], 16)))
                is_escaped = False

            if (cur_chr == escape):
                is_escaped = not is_escaped
                esc_pos = cur_pos if (is_escaped) else -1
                continue

            if (is_escaped):
                if (cur_chr in Env.SPECIAL):
                    cur_chr = Env.SPECIAL[cur_chr]
                elif (cur_chr == "u"):
                    acc_beg_pos = cur_pos + 1
                    acc_end_pos = acc_beg_pos + 4
                    continue
                elif (cur_chr == "x"):
                    acc_beg_pos = cur_pos + 1
                    acc_end_pos = acc_beg_pos + 2
                    continue
                is_escaped = False

            chr_lst.append(cur_chr)

        # If escaped char (by code) is the last one, accumulation
        # action was missed from the loop: fulfilling here

        if is_escaped:
            if (acc_end_pos > 0):
                if (cur_pos >= acc_end_pos - 1):
                    chr_lst.append(chr(int(input[acc_beg_pos:acc_end_pos], 16)))
                elif (esc_pos >= 0):
                    Env.__fail_unescape(input, esc_pos, cur_pos + 1)
            elif (esc_pos >= 0):
                Env.__fail_unescape(input, esc_pos, cur_pos + 1)

        # Join all characters and return the resulting string

        return "".join(chr_lst)

    ###########################################################################

    @staticmethod
    def unquote(
        input: str,
        unescape: bool | None = None,
        strip_spaces: bool = True,
        escapes: str = None,
        expands: str = None,
        hard_quotes: str = None,
        stoppers: str = None,
    ) -> tuple[str, EnvUnquoteInfo]:
        """
        Optionally, remove leading and trailing whitespaces from the copy
        of the input, then remove enclosing quotes if found, then,
        optionally, unescape escaped characters and return the result as
        well as the unquoting info that also contains detected expand
        character (default: $, or the first of $ or % depending on the
        running platform)

        :param input: String to unquote
        :type input: str
        :param escapes: Escape characters: "\\\\\\\\", "\\\\\\\\%"
        :type escapes: str
        :param strip_spaces: True = strip leading and trailing spaces. If
                             quoted, don't strip again after unquoting
        :type strip_spaces: bool
        :param expands: A string of characters where each indicates a start
                        of an env var or an arg expansion: "$%"
        :type expands: str
        :param hard_quotes: A string containing all quote characters that
                            require to ignore escaping: e.g., a single quote
        :type hard_quotes: bool
        :param stoppers: A string of characters where each indicates a string
                         end when found non-escaped and either outside quotes
                         or in an unquoted input: e.g., a line comment: "#"
        :type stoppers: str
        :return: unquoted and, optionally, unescaped input, as well as
                 details: see _EnvUnquoteData_
        :rtype: tuple[str, EnvUnquoteData]
        """

        # Unquote the string first

        info: EnvUnquoteInfo

        _, info = Env.unquote_only(
            input,
            strip_spaces=strip_spaces,
            escapes=escapes,
            expands=expands,
            hard_quotes=hard_quotes,
            stoppers=stoppers
        )

        # If unescape flag is undefined, and input wasn't quoted, override it

        if (unescape is None) and (info.quote_type == EnvQuoteType.NONE):
            unescape = True

        # If no unescape needed, finish

        if not unescape:
            return (info.result, info)

        # Unescape the result

        info.result = Env.unescape(info.result, info.escape)

        # Don't strip whitespaces again if not needed or if input was quoted

        if (not strip_spaces) or (info.quote_type != EnvQuoteType.NONE):
            return (info.result, info)

        # Here, result should be stripped of the whitespaces, so do that

        result: str = info.result

        if result and ((result[0] in string.whitespace) or (
            result[len(result) - 1] in string.whitespace
        )):
            info.result = result.strip()

        # Finish

        return (info.result, info)

    ###########################################################################

    @staticmethod
    def unquote_only(
        input: str,
        strip_spaces: bool = True,
        escapes: str = None,
        expands: str = None,
        hard_quotes: str = None,
        stoppers: str = None,
    ) -> tuple[str, EnvUnquoteInfo]:
        """
        Remove enclosing quotes from a string ignoring everything beyond the
        closing quote ignoring escaped quotes. Raise ValueError if a dangling
        escape or no closing quote found.
        
        In most cases, you'd rather use _Env.unquote()_ that calls this method,
        then expands environment variables, arguments, and unescapes special
        characters.
        
        :param input: String to remove enclosing quotes from
        :type input: str
        :param escape: Escape characters: whichever comes first in the input
                       will be returned in the dedicated info
        :type escapes: str
        :param strip_spaces: True = strip leading and trailing spaces. If
                             quoted, don't strip again after unquoting
        :type strip_spaces: bool
        :param expands: A string of characters where each indicates a start
                        of env var or arg expansion (e.g., "$%")
        :type expands: str
        :param hard_quotes: A string containing all quote characters that
                            require to ignore escaping (e.g., a single quote)
        :type hard_quotes: bool
        :param stoppers: A string of characters where each indicates a string
                         end when found non-escaped and either outside quotes
                         or in an unquoted input (e.g., a line comment: "#")
        :type stoppers: str
        :return: unquoted input and details: see _EnvUnquoteData_
        :rtype: tuple[str, EnvUnquoteData]
        """

        # Initialize

        info = EnvUnquoteInfo(input=input, quote_type=EnvQuoteType.NONE)

        # If the input is None or empty, return the empty string

        if (not input):
            return (info.result, info)

        # Ensure required arguments are populated

        if (not escapes):
            escapes = EnvUnquoteInfo.DEFAULT_ESCAPES
        if (not expands):
            expands = EnvUnquoteInfo.DEFAULT_EXPANDS

        # Initialize position beyond the last character and results

        end_pos: int = 0
        info.result = input.lstrip() if (strip_spaces) else input

        if (not info.result):
            return (info.result, info)

        # Initialise quote and determine quote type

        info.quote = info.result[0]

        if (info.quote == '"'):
            info.quote_type = EnvQuoteType.DOUBLE
        elif (info.quote == "'"):
            info.quote_type = EnvQuoteType.SINGLE
        else:
            info.quote = ""

        # Initialise flags for escaping and quoting

        has_stoppers: bool = True if stoppers else False
        is_escaped: bool = False
        is_quoted: bool = info.quote_type != EnvQuoteType.NONE

        # Avoid Nones

        if (hard_quotes is None):
            hard_quotes = "'"

        # No escape is relevant if the given quote is the hard one

        if is_quoted and (info.quote in hard_quotes):
            escapes = ""

        # Loop through each input character and analyze

        for cur_chr in info.result:
            # Advance the end position and skip opening quote if present

            end_pos = end_pos + 1

            if (end_pos == 1) and is_quoted:
                continue

            # If an escape encountered, flip the flag and loop

            if (cur_chr in escapes):
                info.escape = cur_chr
                is_escaped = not is_escaped
                continue

            # When a quote is encountered, if escaped, loop, else,
            # this quote is the closing one, so return the result.

            if (cur_chr == info.quote):
                if is_quoted and (info.quote in hard_quotes):
                    is_quoted = False
                    break
                if (is_escaped):
                    is_escaped = False
                    continue
                if (is_quoted):
                    is_quoted = False
                    break
                else:
                    continue

            # Set expand character if found first time

            if (cur_chr in expands):
                if (not info.expand) and (not is_escaped):
                    info.expand = cur_chr

            # Break out if the stopper character was encountered outside
            # the quotes, and it was not escaped

            if (not is_quoted) and (not is_escaped):
                if has_stoppers and (cur_chr in stoppers):
                    end_pos = end_pos - 1
                    break

            # For any other character, discard is_escaped

            is_escaped = False

        # Check the malformed input

        if is_escaped:
            raise ValueError(f"A dangling escape found in: {input}")

        if is_quoted:
            raise ValueError(f"Unterminated quoted string: {input}")

        # Calculate the unquoted substring

        if info.quote_type == EnvQuoteType.NONE:
            beg_pos = 0
        else:
            beg_pos = 1
            end_pos = end_pos - 1

        # Extract the unquoted substring

        info.result = info.result[beg_pos:end_pos]

        # Strip trailing spaces if needed, but only if the original input
        # was not quoted

        if strip_spaces and (info.quote_type == EnvQuoteType.NONE):
            info.result = info.result.rstrip()

        # Return the result

        return (info.result, info)

    ###########################################################################

    @staticmethod
    def __fail_unescape(input: str, beg_pos: int, end_pos: int):
        """
        Error handler for Env.unescape()
        
        :param input: Full string at fault
        :type input: str
        :param beg_pos: Starting position of the fragment at fault
        :type beg_pos: int
        :param end_pos: Ending position of the fragment at fault
        :type end_pos: int
        :return: Raise exception
        :rtype: None
        """

        dtl: str = input[beg_pos:end_pos]

        raise ValueError(
            f"Incomplete escape sequence from [{beg_pos}]: \"{dtl}\" in \"{input}\""
        )

    ###########################################################################

    @staticmethod
    def __parse_escapes(
        input: str,
        match: re.Match,
        min_escape_count: int
    ) -> tuple[tuple[Any, ...], str, str]:
        """
        :param input: The string being scanned
        :type input: str
        :param match: Analyze match and return groups as well as unescaped
                      escapes (twice less) and the no_action string. When the
                      latter is not None, it tells to return that immediately
                      from the replacer, as there is nothing to unescape or
                      expand
        :type match: re.Match
        :param min_escape_count: Pass as 0 for env vars' and args' expansions
                                 (all escapes should compensate each other).
                                 Pass as 1 for unescapes (there should be 1
                                 left after the rest of escapes compensate
                                 each other)
        :type min_escape_count: int
        :param expand_info: Rules for expansion and unescaping
        :type expand_info: EnvExpandInfo
        :return: (groups, unescaped-escapes, no_action)
        :rtype: tuple[tuple[Any, ...], str, str]
        """

        # If the input is void, return the empty string

        if not match:
            return (None, "", input)

        # Initialise

        groups: tuple[Any, ...] = match.groups()
        escapes: str = groups[0]
        escape_count: int = len(escapes)
        no_action: str = ""

        if (escape_count > 0):
            escapes = escapes[0] * (escape_count // 2)
        
        # If this number of escapes dictate to ignore the rest, set
        # no_action to the value that should be returned from caller
        # without any further interpretation

        if ((escape_count % 2) != min_escape_count):
            no_action = escapes + match.string[escape_count:]

        # All components are ready, return those

        return (groups, escapes, no_action)


###############################################################################
