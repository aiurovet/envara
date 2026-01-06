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
import sys
from typing import Any, Final

from env_expand_flags import EnvExpandFlags
from env_expand_info import EnvExpandInfo
from env_platform_stack_flags import EnvPlatformStackFlags
from env_quote_type import EnvQuoteType

###############################################################################


class Env:
    """
    Class for string expansions
    """

    # Flag indicating whether the script is running under Windows or not
    IS_POSIX: Final[bool] = os.sep == "/"

    # Flag indicating whether the script is running under Windows or not
    IS_WINDOWS: Final[bool] = os.sep == "\\"

    # A text indicating any platform, but not empty
    PLATFORM_ANY: Final[str] = "any"

    # A text indicating a POSIX-compatible platform
    PLATFORM_POSIX: Final[str] = "posix"

    # A text indicating a Windows-compatible platform
    PLATFORM_WINDOWS: Final[str] = "windows"

    # A text indicating the running platform
    PLATFORM_THIS: Final[str] = sys.platform.lower()

    # Expansion/unescaping info - MSDOS-style
    __msdos_info: EnvExpandInfo = EnvExpandInfo(
        expand="%",
        escape="^",
        pat_esc="(\\^)+(x([\\dA-Fa-f]{2})|u([\\dA-Fa-f]{4})|.)",
        pat_var="(\\^*)(%)([A-Za-z_][A-Za-z_\\d]*)(%)",
        pat_arg="(\\^*)(%)([\\d]+)(%)",
    )

    # Expansion/unescaping info - POSIX-style
    __posix_info: EnvExpandInfo = EnvExpandInfo(
        expand="$",
        escape="\\\\",
        pat_esc="(\\\\+)(x([\\dA-Fa-f]{2})|u([\\dA-Fa-f]{4})|.)",
        pat_var="(\\\\*)\\$({?)([A-Za-z_][A-Za-z_\\d]*)(}?)",
        pat_arg="(\\\\*)\\$({?)([\\d]+)(}?)",
    )

    __powsh_info: EnvExpandInfo = EnvExpandInfo(
        expand="$",
        escape="`",
        pat_esc="(`+)(x([\\dA-Fa-f]{2})|u([\\dA-Fa-f]{4})|.)",
        pat_var="(`*)\\$({?)([A-Za-z_][A-Za-z_\\d]*)(}?)",
        pat_arg="(`*)\\$({?)([\\d]+)(}?)",
    )

    # Internal dictionary: regex => list-of-platform-names
    __platform_map: dict[str, list[str]] = {
        "": ["", PLATFORM_ANY, PLATFORM_POSIX],
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
        args: list[str] = None,
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
                    result = Env.expandargs(result, args)
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
    def expandargs(input: str, args: list[str] = None) -> str:
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
        prefix: str = None,
        suffix: str = None,
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
    def quote(input: str, type: EnvQuoteType = EnvQuoteType.DOUBLE) -> str:
        """
        Embrace input with quotes. Neither leading, nor trailing white spaces
        removed before checking the leading quotes. Use .strip() yourself
        before calling this method if needed.

        :param input: String being expanded
        :type input: str
        :return: Quoted string with possible quotes and escape characters from
                 the inside being escaped
        :rtype: str
        """

        # Initialise the result

        result = "" if (input is None) else input

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
            if Env.ESCAPE in result:
                result = result.replace(Env.ESCAPE, Env.ESCAPE_ESCAPED)
            result = result.replace(quote, f"{Env.ESCAPE}{quote}")

        return f"{quote}{result}{quote}"

    ###########################################################################

    @staticmethod
    def remove_line_comment(input: str) -> str:
        """
        Remove the input's line comment: from # (hash symbol) outside the
        quotes (if any) to the end of the whole string, as the input is
        treated as a single line. The point is that in case of a multi-line
        processing, it is inevitable to break the input into separate lines
        and process those independently.

        :param input: String being truncated
        :type input: str
        :return: string with the line comment removed, and an indicator of
                 what type of quote was encountered
        :rtype: (str, EnvQuote)
        """

        # If input is None or empty, return the empty string

        if not input:
            return ""

        # Find the start of a line comment in the input, and
        # return the input unchanged if a line comment was not
        # found

        beg_pos = input.find("#")

        if beg_pos < 0:
            return input

        # Find the end of a line considering either POSIX or Windows
        # line breaks

        end_pos = input.find("\n")

        if (end_pos >= 2) and input[end_pos - 2] == "\r":
            end_pos = end_pos - 1

        # Set result to the substring from the beginning to the line comment
        # start, then remove trailing blanks and return the result

        return input[0:beg_pos].rstrip()

    ###########################################################################

    @staticmethod
    def unescape(input: str) -> str:
        """
        Unescape '\\t', '\\n', etc.

        :param input: Input string to unescape escaped characters in
        :type input: str
        :return: Unescaped string
        :rtype: str
        """

        if not input:
            return ""

        if Env.ESCAPE not in input:
            return input

        def matcher(x: re.Match):
            return x.group(1)

        return Env.RE_DROP_ESCAPE.sub(matcher, input).encode().decode("unicode_escape")

    ###########################################################################

    @staticmethod
    def unquote(input: str, unescape: bool = True) -> tuple[str, EnvQuoteType]:
        """
        Remove the input's embracing quotes. Neither leading, nor trailing
        white spaces removed before checking the leading quotes. Use .strip()
        yourself before calling this method if needed.

        :param input: String being expanded
        :type input: str
        :param unescape: If True, and input is not single-quoted, unescape
                         escaped characters
        :type unscape: bool
        :return: Unquoted string, and a number indicating the level of quoting:
                 0 = not quoted, 1 = single-quoted, 2 = double-quoted
        :rtype: str
        """

        # If input is None or empty, return the empty string

        if not input:
            return ("", EnvQuoteType.NONE)

        # Initialise result string to be returned, and the first character

        prefix = "" if (unescape) else Env.ESCAPE
        result = input
        c1 = result[0]

        # Initialise quote_type

        if c1 == "'":
            prefix = Env.ESCAPE
            quote_type = EnvQuoteType.SINGLE
        elif c1 == '"':
            quote_type = EnvQuoteType.DOUBLE
        else:
            c1 = ""
            quote_type = EnvQuoteType.NONE

        # Hide interfering characters if needed

        was_protected = Env.HIDE_01 in result

        if not was_protected:
            result = result.replace(Env.ESCAPE_ESCAPED, Env.HIDE_01)
            if quote_type != EnvQuoteType.SINGLE:
                result = result.replace(f'{Env.ESCAPE}"', Env.HIDE_02)

        if quote_type == EnvQuoteType.SINGLE:

            # Validate and unquote a single-quoted input

            end_pos = result.find(c1, 1)

            if end_pos < 0:
                raise ValueError(f"Unterminated single-quoted string: {input}")

            result = result[1:end_pos]
            quote_type = EnvQuoteType.SINGLE

        elif quote_type == EnvQuoteType.DOUBLE:

            # Validate and unquote a double-quoted input

            end_pos = result.find(c1, 1)

            if end_pos < 0:
                raise ValueError(f"Unterminated double-quoted string: {input}")

            result = result[1:end_pos]

        # Unescape escaped characters if needed

        if unescape:
            result = Env.unescape(result)

        # Unhide interfering characters if needed

        if not was_protected:
            if quote_type != EnvQuoteType.SINGLE:
                result = result.replace(Env.HIDE_02, f"{prefix}{c1}")
            result = result.replace(Env.HIDE_01, f"{prefix}{Env.ESCAPE}")

        return (result, quote_type)


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
                      escapes (twice less) and the immediate string. When the
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
        :return: (groups, unescaped-escapes, immediate)
        :rtype: tuple[tuple[Any, ...], str, str]
        """

        # If the input is void, return the empty string

        if not match:
            return (None, "", input)

        # Initialise

        groups: tuple[Any, ...] = match.groups()
        escapes: str = groups[0]
        esc_len: int = len(escapes)
        immediate: str = ""

        if (esc_len > 0):
            escapes = escapes[0] * (esc_len // 2)
        
        # If this number of escapes dictate to ignore the rest, set
        # immediate to the value that should be returned from caller

        if ((esc_len % 2) == min_escape_count):
            immediate = escapes + match.string[esc_len:]

        # All components are ready, return those

        return (groups, escapes, immediate)

###############################################################################
