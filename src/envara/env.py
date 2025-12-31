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
import sys
from typing import Final

###############################################################################
# Implementation
###############################################################################

class Env:
    """
    Class for string expansions
    """

    FLAGS: Final = re.DOTALL | re.UNICODE

    CONDITIONAL_RE: Final = re.compile(
        r'\$\{(\d+|[A-Za-z_!][A-Za-z_\d]*)([:]?)([\+\-\=\?])([^}]*)\}', flags=FLAGS)

    EXPLICIT_RE: Final = re.compile(
        r'(\$(\d+|[A-Za-z_][A-Za-z_\d]*))|(\${(\d+|[A-Za-z_!][A-Za-z_\d]*)})', flags=FLAGS)

    ###########################################################################

    @staticmethod
    def expand(input: str, args: list[str] = None, keep_unknown: bool = False) -> str:
        """
        Return given string expanded with environment variables and,
        optionally, with arguments, following UNIX conventions: $ABC, ${ABC},
        and generally, ${[!]ABC[:][-+=?]${...}}.
        
        Windows notation %ABC%, and PowerShell's $env:ABC, are ignored
        
        :param input: Input string to expand
        :type input: str
        :param args: List of arguments to expand from $1, ...
        :type input: str
        :return: Expanded string
        :rtype: str
        """

        # Initialize variables

        argc: int = 0 if (args is None) else len(args)
        prev: str = ''

        # Hide escaped characters

        next: str = (input or prev)\
            .replace(r'\\', '\x01')\
            .replace(r'\$', '\x02')

        # Repeat expansions in a loop to ensure all complex embeddings
        # get resolved

        while (next != prev):
            prev = next

            next = Env.__expand_explicit_patterns(
                next, argc, args, keep_unknown)

            next = Env.__expand_conditional_patterns(
                next, argc, args, argc, keep_unknown)

        # Unhide escaped characters

        next = next\
            .replace('\x02', r'\$')\
            .replace(r'\x01', r'\\')

        return next

    ###########################################################################

    @staticmethod
    def __expand_conditional_patterns(input: str, arg_cnt: int, args: list[str] = None, keep_unknown: bool = False) -> str:
        """
        Return given string expanded in a single pass with the environment
        variables' conditional pattern and, optionally, conditional arguments'
        pattern
        
        :param input: Input string to expand
        :type input: str
        :param args: List of arguments to expand from $1, ...
        :type input: str
        :return: Expanded string
        :rtype: str
        """

        # Initialize the previous and current value of the string being expanded

        next_pos = 0
        result = input

        # Loop until there is no more change in the string being expanded

        while True:
            # Search again and break if nothing found

            match = Env.CONDITIONAL_RE.search(result, pos=next_pos)

            if (match is None):
                break

            # Get the full pattern found, the key/index and position for
            # the next check

            found = match.group(0)
            key = match.group(1)
            next_pos = match.start(0)

            # Try to parse the index

            arg_idx = None if (args is None) else Env.__try_parse_int(key)

            if (arg_idx is None):
                value, key = Env.__get_var(key, keep_unknown)
            else:
                value = Env.__get_arg(args, arg_idx, arg_cnt, keep_unknown)

            # Get the action (question mark, equal sign, plus or minus) as
            # well as the empty-value-as-None flag (colon)

            action = match.group(3)
            has_colon = True if (match.group(2)) else False

            # Set the flag indicating whether the alternative value should
            # be used or not

            use_alt = \
                (has_colon and (not value)) or \
                ((not has_colon) and (value is None))

            # Get the alternative value if needed

            alt_val = match.group(4) if (use_alt) else ''

            # Do not expand if the substitution is not found, and the matched
            # pattern should be kept unchanged

            if ((value is None) and keep_unknown):
                next_pos += len(found)

                if (use_alt and (action == '?')):
                    print(alt_val, file=sys.stderr)

                continue

            # Set the value depending on action and the above flags

            match action:
                case '?':
                    if (use_alt):
                        print(alt_val, file=sys.stderr)
                        value = ''
                case '=':
                    if (use_alt):
                        value = alt_val
                        if (key):
                            os.environ[key] = value
                case '-':
                    if (use_alt):
                        value = alt_val
                case '+':
                    if (not use_alt):
                        value = alt_val

            # Perform the actual expansion

            result = result.replace(found, value)
            next_pos += len(value) - len(found)

        return result

    ###########################################################################

    @staticmethod
    def __expand_explicit_patterns(
        input: str, arg_cnt: int,
        args: list[str] = None, keep_unknown: bool = False) -> str:
        """
        Return given string expanded in a single pass with the environment
        variables' plain pattern and, optionally, arguments' plain pattern
        
        :param input: Input string to expand
        :type input: str
        :param args: List of arguments to expand from $1, ...
        :type args: str
        :param keep_unknown: If True, do not replace the found patterns with
                             the empty string
        :type input: str
        :return: Expanded string
        :rtype: str
        """

        # Initialize the previous and current value of the string being
        # expanded

        next_pos = 0
        result = input

        # Loop until there is no more change in the string being expanded

        while True:
            # Search continuosly until nothing found

            match = Env.EXPLICIT_RE.search(result, pos=next_pos)

            if (match is None):
                break

            # Get the full pattern found, the key/index and position for
            # the next check

            end_grp_pos = match.end(1)

            if (end_grp_pos >= 0):
                found = match.group(1)
                key = match.group(2)
            else:
                end_grp_pos = match.end(3)
                found = match.group(3)
                key = match.group(4)

            next_pos = end_grp_pos

            # Try to parse an index if the arguments passed

            arg_idx = None if (arg_cnt <= 0) else Env.__try_parse_int(key)

            # Get the value from the environment or the arguments

            if (arg_idx is None):
                value, _ = Env.__get_var(key, keep_unknown)
            else:
                value = Env.__get_arg(args, arg_idx, arg_cnt, keep_unknown)

            # Perform the actual replacement

            if (value is None):
                continue

            result = result.replace(found, value)
            next_pos += len(value) - len(found)

        return result

    ###########################################################################

    @staticmethod
    def __get_arg(
        args: list[str], index: int, count: int,
        keep_unknown: bool = False) -> str:
        """
        Soft argument getter: if index was not found, return None or the empty
        string depending on keep_unknown
        
        :param args: The list of arguments
        :type args: list[str]
        :param keep_unknown: If True, and the index is not in bounds,
                             return None. Otherwise, if the index is not in
                             bounds, return the empty string
        :type keep_unknown: bool
        :return: The value of the environment variable if found, or None/empty,
                 depending on keep_unknown
        :rtype: str
        """

        # If index is out of bounds key, return None or the empty string
        # depending on keep_unknown

        if ((index < 1) or (index > count)):
            return None if (keep_unknown) else ''

        # If the index is in boundsm, return the value

        return args[index - 1]

    ###########################################################################

    @staticmethod
    def __get_var(key: str, keep_unknown: bool = False) -> tuple[str, str]:
        """
        Soft environment variable getter: if key was not found, return None
        or the empty string depending on keep_unknown; if key starts with
        the exclamation mark, retrieve the value of the variable by reduced
        key, then use it as a key to get another value
        
        :param key: The name of the variable
        :type key: str
        :param keep_unknown: If True, and the key is not present, return None
                             Otherwise, if the key is not present, return empty
        :type keep_unknown: bool
        :return: The value of the environment variable if found, or None/empty,
                 depending on keep_unknown as well as the alternative key or None
                 depending on whether the original one had the exclamation mark
                 as prefix or not
        :rtype: tuple[str, str]
        """

        alt_key: str = None

        # If key is prefixed with the exclamation mark, exclude it and retrieve
        # the value, then set that as a key to another value

        if ((len(key) > 1) and (key[0] == '!')):
            key = key[1:]
            key = os.environ[key] if (key in os.environ) else None
            alt_key = key

        # If key is None or empty, return None or the empty string depending on
        # keep_unknown

        if (not key):
            return (None if (keep_unknown) else '', alt_key)

        # If key is found, return the value. Otherwise, if keep_unknown,
        # return None

        if (key in os.environ):
            return (os.environ[key], alt_key)
        elif (keep_unknown):
            return (None, alt_key)

        # If got here, return the empty string

        return ('', alt_key)

    ###########################################################################

    @staticmethod
    def __try_parse_int(input: str) -> int | None:
        """
        Return integer parsed from a string or None if that is impossible
        
        :param input: String to parse
        :type input: str
        :return: Result of parsing or None
        :rtype: int
        """

        try:
            return int(input)
        except:
            return None

###############################################################################
