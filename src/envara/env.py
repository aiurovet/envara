###############################################################################
# svg2many (C) Alexander Iurovetski 2025
#
# A class to read series of key=value lines from a text file and set those
# as environment variables.
#
# Differs from the standard dotenv.load_dotenv by the ability to expand
# existing environment variables in the new values before these are added.
#
# This class also allows to avoid unnecessary dependency: easy to implement.
###############################################################################

import os
import re
from enum import IntEnum, IntFlag
import sys
from typing import Final

###############################################################################
# Flags impacting string expansion behaviour
###############################################################################

class EnvExpandFlags(IntFlag):
    # No flag set
    NONE = 0

    # Expand escaped characters: \\ or `\`, \n or `n, \uNNNN or `uNNNN`, etc.
    # (depends on NATIVE_ESCAPE flag)
    DECODE_ESCAPED = (1<<0)

    # Remove hash '#' (outside the quotes if found) and everything beyond that
    REMOVE_LINE_COMMENT = (1<<2)

    # Remove leading and trailing quote, don't expand single-quoted str: '...'
    REMOVE_QUOTES = (1<<3)

    # If a string is embraced in apostrophes, don't expand it
    SKIP_SINGLE_QUOTED = (1<<4)

    # Default set of flags
    DEFAULT = (DECODE_ESCAPED | REMOVE_LINE_COMMENT | \
               REMOVE_QUOTES | SKIP_SINGLE_QUOTED)

###############################################################################

class EnvQuoteType(IntEnum):
    # String with no leading quote
    NONE = 0,

    # Single-quoted string
    SINGLE = 1,

    # Double-quoted string
    DOUBLE = 2

###############################################################################
# Implementation
###############################################################################

class Env:
    """
    Class for string expansions
    """

    # Regex to find references to arguments ($n or ${n} or %n) by 1-based index
    # % though will work under Windows only
    ARGS_RE: Final = re.compile(
        r'\$(\d+)|\${(\d+)}|%(\d+)', flags=(re.DOTALL | re.UNICODE))

    # Flag indicating whether the script is running under Windows or not
    IS_WINDOWS: Final = os.sep == '\\'

    ###########################################################################

    @staticmethod
    def expand(
        input: str, args: list[str] = None,
        flags: EnvExpandFlags = EnvExpandFlags.DEFAULT):
        """
        Unquote the input if required, remove trailing line comment if
        required, expand the result with the arguments if required, expand
        the result with the environment variables' values. The method follows
        minimal POSIX conventions: $ABC and ${ABC}, as well as %ABC% on Windows
        
        :param input: Input string to expand
        :type input: str
        :param args: List of arguments to expand from $1, ...
        :type input: str
        :return: Expanded string
        :rtype: str
        """

        # For input as None or the empty string, return empty string

        if (not input):
            return ''

        # If the user indicator is found, expand the string

        quote_type = EnvQuoteType.NONE
        result = input

        # If unquoting requested, do that treating a single-quoted input
        # as literal (no further expansion) if required

        if (flags & EnvExpandFlags.REMOVE_QUOTES):
            result, quote_type = Env.unquote(result)

            if ((quote_type == EnvQuoteType.SINGLE) and \
                (flags & EnvExpandFlags.SKIP_SINGLE_QUOTED)):
                return result

        # Remove line comment if required

        if ((quote_type == EnvQuoteType.NONE) and \
            (flags & EnvExpandFlags.REMOVE_LINE_COMMENT)):
            result = Env.remove_line_comment(result)

        # If the user indicator is found, expand the string

        if ('~' in result):
            result = os.path.expanduser(result)

        # Expand arguments, then the environment variables if the respective
        # prefix is found in the string

        if (('$' in result) or (Env.IS_WINDOWS and ('%' in result))):
            result = Env.expandargs(result, args)
            result = os.path.expandvars(result)

        # Expand escaped characters like \t, \n, \xNN, \uNNNN if needed

        if ((flags & EnvExpandFlags.DECODE_ESCAPED) and ('\\' in result)):
            result = result.encode().decode('unicode_escape')

        return result

    ###########################################################################

    @staticmethod
    def expandargs(input: str, args: list[str] = None) -> str:
        """
        Expand references to an array of arguments by index
        
        :param input: String being expanded
        :type input: str
        :param args: List of arguments to refer to
        :type args: list[str]
        :return: Expanded string
        :rtype: str
        """

        if (not input):
            return ''

        arg_cnt = len(args)

        def matcher(match):
            idx_str = match.group(1) or match.group(2)

            if ((not idx_str) and Env.IS_WINDOWS):
                idx_str = match.group(3)

                if (not idx_str):
                    return match.group(0)

            idx_int = int(idx_str) - 1

            if ((idx_int >= 0) and (idx_int < arg_cnt)):
                return args[idx_int]

            return match.group(0)

        return Env.ARGS_RE.sub(matcher, input)

    ###########################################################################

    @staticmethod
    def remove_line_comment(input: str) -> tuple[str, EnvQuoteType]:
        """
        Remove the input's line comment: from # outside the quotes to the
        end of the first line, and return the result. If the input is a
        multi-line string, only the first line will be reduced, and the rest
        appended
        
        :param input: String being truncated
        :type input: str
        :return: string with the line comment removed, and an indicator of
                 what type of quote was encountered
        :rtype: (str, EnvQuote)
        """

        # If input is None or empty, return the empty string

        if (not input):
            return ''

        # Find the start of a line comment in the input, and
        # return the input unchanged if a line comment was not
        # found

        beg_pos = input.find('#')

        if (beg_pos < 0):
            return input

        # Find the end of a line considering either POSIX or Windows
        # line breaks

        end_pos = input.find('\n')

        if ((end_pos >= 2) and input[end_pos - 2] == '\r'):
            end_pos = end_pos - 1

        # Set result to the substring from the beginning to the line comment
        # start, then append everything beyond the line end if found

        result = input[0:beg_pos].rstrip()

        if ((end_pos >= 0) and (end_pos < len(input) - 1)):
            result += input[end_pos:]

        # Return the result with the trailing spaces removed

        return result

    ###########################################################################

    @staticmethod
    def unquote(input: str) -> tuple[str, EnvQuoteType]:
        """
        Remove the input's embracing quotes. Neither leading, nor trailing
        white spaces removed before checking the leading quotes. Use .strip()
        yourself before calling this method if needed.
        
        :param input: String being expanded
        :type input: str
        :return: Unquoted string, and a number indicating the level of quoting:
                 0 = not quoted, 1 = single-quoted, 2 = double-quoted
        :rtype: str
        """

        # If input is None or empty, return the empty string

        if (not input):
            return ('', EnvQuoteType.NONE)

        # Initialise result to be returned as well as the first character

        result = input
        c1 = result[0]

        # Validate and unquote a single-quoted input, then return the
        # result if required

        if (c1 == "'"):
            end_pos = input.find(c1, 1)

            if (end_pos < 0):
                raise ValueError(f'Unterminated single-quoted string: {input}')

            return (input[1:end_pos], EnvQuoteType.SINGLE)

        # Validate and unquote a double-quoted input as well as replace
        # escaped double-quotes with the plain ones

        if (c1 == '"'):
            result = result.replace('\\"', '\x01')
            end_pos = result.find(c1, 1)

            if (end_pos < 0):
                raise ValueError(f'Unterminated double-quoted string: {input}')

            result = result[1:end_pos].replace('\x01', '"')
            
            return (result, EnvQuoteType.DOUBLE)

        return (result, EnvQuoteType.NONE)

###############################################################################
