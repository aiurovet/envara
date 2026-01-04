#!/usr/bin/env pytest

###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# Tests for Env
###############################################################################

import os
import pytest

from env import Env, EnvExpandFlags, EnvQuoteType
from env_platform_stack_flags import EnvPlatformStackFlags

###############################################################################


class TestDecodeEscaped:
    """Test suite for Env.decode_escaped method"""

    @pytest.mark.parametrize(
        "input, expected",
        [
            (None, ""),
            ("", ""),
            ("A b c", "A b c"),
            ("A\\tb\\tc", "A\tb\tc"),
            ("A\\ \\N\\+\\u0042b\\a\\x41c", "A N+Bb\aAc"),
        ],
    )
    def test_decode_escaped(
        self,
        input: str,
        expected: str,
    ):

        # Call the method
        result = Env.decode_escaped(input)

        # Verify result matches expected
        assert result == expected


###############################################################################


class TestExpand:
    """Test suite for Env.expand method"""

    @pytest.mark.parametrize(
        "platform, input, env, args, flags, expected",
        [
            ("", "", {}, [], EnvExpandFlags.NONE, ""),
            ("", "a$1b", {}, ["x"], EnvExpandFlags.NONE, "axb"),
            ("", "a${1}b", None, ["x"], EnvExpandFlags.NONE, "axb"),
            ("", "a$a${b}", {"a": "efg1"}, [], EnvExpandFlags.NONE, "aefg1${b}"),
            ("", "a#$a${b}", {"a": "efg1"}, [], EnvExpandFlags.REMOVE_LINE_COMMENT, "a"),
            (
                "posix",
                "'a $2 $a \\${b}'",
                {"a": "efg1", "b": "xx"},
                ["A1", "A2"],
                EnvExpandFlags.REMOVE_LINE_COMMENT
                | EnvExpandFlags.DECODE_ESCAPED
                | EnvExpandFlags.REMOVE_QUOTES
                | EnvExpandFlags.SKIP_SINGLE_QUOTED,
                "a $2 $a \\${b}",
            ),
            (
                "posix",
                '"a $2 ~ $a \\${b}"',
                {"a": "efg1", "b": "xx"},
                ["A1", "A2"],
                EnvExpandFlags.REMOVE_LINE_COMMENT
                | EnvExpandFlags.DECODE_ESCAPED
                | EnvExpandFlags.REMOVE_QUOTES
                | EnvExpandFlags.SKIP_SINGLE_QUOTED,
                "a A2 ~ efg1 ${b}",
            ),
            (
                "windows",
                "a %2 $a #${b}",
                {"a": "efg1", "b": "xx"},
                ["A1", "A2"],
                EnvExpandFlags.REMOVE_LINE_COMMENT
                | EnvExpandFlags.DECODE_ESCAPED
                | EnvExpandFlags.REMOVE_QUOTES
                | EnvExpandFlags.SKIP_SINGLE_QUOTED,
                "a A2 efg1",
            ),
            (
                "windows",
                '"a %20 ~ $a \\${b}"',
                {"a": "efg1", "b": "xx"},
                ["A1", "A2"],
                EnvExpandFlags.REMOVE_LINE_COMMENT
                | EnvExpandFlags.DECODE_ESCAPED
                | EnvExpandFlags.REMOVE_QUOTES
                | EnvExpandFlags.SKIP_SINGLE_QUOTED,
                "a %20 ~ efg1 ${b}",
            ),
            (
                "posix",
                '"a $1 ~ $xyz \\${b}"',
                {"a": "efg1", "b": "xx"},
                ["A1", "A2"],
                EnvExpandFlags.REMOVE_LINE_COMMENT
                | EnvExpandFlags.DECODE_ESCAPED
                | EnvExpandFlags.REMOVE_QUOTES
                | EnvExpandFlags.SKIP_SINGLE_QUOTED,
                "a A1 ~ $xyz ${b}",
            ),
            (
                "posix",
                "'a $2 $a #${b}'",
                {"a": "efg1", "b": "xx"},
                ["A1", "A2"],
                EnvExpandFlags.REMOVE_LINE_COMMENT
                | EnvExpandFlags.DECODE_ESCAPED
                | EnvExpandFlags.REMOVE_QUOTES
                | EnvExpandFlags.SKIP_SINGLE_QUOTED,
                "a $2 $a #${b}",
            ),
            (
                "posix",
                "~/abc",
                {"a": "efg1", "b": "xx"},
                ["A1", "A2"],
                EnvExpandFlags.REMOVE_LINE_COMMENT
                | EnvExpandFlags.DECODE_ESCAPED
                | EnvExpandFlags.REMOVE_QUOTES
                | EnvExpandFlags.SKIP_SINGLE_QUOTED,
                os.path.expanduser("~/abc"),
            ),
            (
                "posix",
                f"~{os.sep}$a{os.sep}${{b}}",
                {"a": "efg1", "b": "xx"},
                ["A1", "A2"],
                EnvExpandFlags.REMOVE_LINE_COMMENT
                | EnvExpandFlags.DECODE_ESCAPED
                | EnvExpandFlags.REMOVE_QUOTES
                | EnvExpandFlags.SKIP_SINGLE_QUOTED,
                os.path.expanduser("~") + f"{os.sep}efg1{os.sep}xx",
            ),
        ],
    )
    def test_expand(
        self,
        platform: str,
        input: str,
        env: dict[str, str],
        args: list[str],
        flags: EnvExpandFlags,
        expected: str,
    ):

        # Arrange
        keys_to_clear = list((env or {}).keys())
        for k, v in (env or {}).items():
            os.environ[k] = v

        if (platform == "posix"):
            Env.IS_POSIX = True
            Env.IS_WINDOWS = False
        elif (platform == "windows"):
            Env.IS_POSIX = False
            Env.IS_WINDOWS = True
        else:
            Env.IS_POSIX = False
            Env.IS_WINDOWS = False

        # Call the method
        result = Env.expand(input, args, flags)

        # Verify result matches expected
        assert result == expected

        # Cleanup
        for k in keys_to_clear:
            os.environ.pop(k, None)


###############################################################################


class TestExpandargs:
    """Test suite for Env.expandargs method"""

    @pytest.mark.parametrize(
        "input, args, expected",
        [
            (None, [], ""),
            ("", [], ""),
            ("a b c", [], "a b c"),
            ("a$1 b ${2}9", [], "a$1 b ${2}9"),
            ("a$1 b ${2}9", ["A1"], "aA1 b ${2}9"),
            ("a$1 b ${2}9", ["A1", "A2"], "aA1 b A29"),
            ("a$1 b $29", ["A1", "A2"], "aA1 b $29"),
        ],
    )
    def test_expandargs(self, input: str, args: list[str], expected: str):

        # Call the method
        result = Env.expandargs(input, args)

        # Verify result matches expected
        assert result == expected


###############################################################################


class TestGetPlatformStack:
    """Test suite for Env.expandargs method"""

    @pytest.mark.parametrize(
        "type, platform, flags, prefix, suffix, expected",
        [
            ("P", "linux3", EnvPlatformStackFlags.NONE, None, None, "posix, linux"),
            (
                "P",
                "linux3",
                EnvPlatformStackFlags.ADD_EMPTY,
                None,
                None,
                ", posix, linux",
            ),
            (
                "P",
                "linux3",
                EnvPlatformStackFlags.ADD_ANY,
                None,
                None,
                "any, posix, linux",
            ),
            (
                "P",
                "linux3",
                EnvPlatformStackFlags.ADD_ANY | EnvPlatformStackFlags.ADD_EMPTY,
                None,
                None,
                ", any, posix, linux",
            ),
            (
                "P",
                "linux3",
                EnvPlatformStackFlags.ADD_CURRENT,
                None,
                None,
                "posix, linux, linux3",
            ),
            (
                "P",
                "linux3",
                EnvPlatformStackFlags.ADD_MAX,
                None,
                None,
                ", any, posix, linux, linux3",
            ),
            (
                "P",
                "linux3",
                EnvPlatformStackFlags.ADD_MAX,
                ".",
                ".env",
                ".env, .any.env, .posix.env, .linux.env, .linux3.env",
            ),
            (
                "P",
                "darwin",
                EnvPlatformStackFlags.ADD_MAX,
                ".",
                ".env",
                ".env, .any.env, .posix.env, .bsd.env, .darwin.env, .macos.env",
            ),
            (
                "P",
                "macos",
                EnvPlatformStackFlags.ADD_MAX,
                ".",
                ".env",
                ".env, .any.env, .posix.env, .bsd.env, .darwin.env, .macos.env",
            ),
            (
                "P",
                "ios",
                EnvPlatformStackFlags.ADD_MAX,
                None,
                None,
                ", any, posix, bsd, ios",
            ),
            (
                "P",
                "aix5",
                EnvPlatformStackFlags.ADD_MAX,
                None,
                None,
                ", any, posix, aix, aix5",
            ),
            (
                "P",
                "cygwin",
                EnvPlatformStackFlags.ADD_MAX,
                None,
                None,
                ", any, posix, cygwin",
            ),
            (
                "P",
                "msys",
                EnvPlatformStackFlags.ADD_MAX,
                None,
                None,
                ", any, posix, msys",
            ),
            (
                "P",
                "java",
                EnvPlatformStackFlags.ADD_MAX,
                None,
                None,
                ", any, posix, java",
            ),
            (
                "W",
                "java",
                EnvPlatformStackFlags.ADD_MAX,
                None,
                None,
                ", any, windows, java",
            ),
            ("", "vms", EnvPlatformStackFlags.ADD_MAX, None, None, ", any, vms"),
            (
                "W",
                "windows",
                EnvPlatformStackFlags.ADD_MAX,
                None,
                None,
                ", any, windows",
            ),
        ],
    )
    def test_get_platform_stack(
        self,
        type: str,
        platform: str,
        flags: EnvPlatformStackFlags,
        prefix: str,
        suffix: str,
        expected: str,
    ):
        Env.IS_POSIX = True if (type == "P") else False
        Env.IS_WINDOWS = True if (type == "W") else False
        Env.PLATFORM_THIS = platform
        Env._Env__platform_map[".+"] = [platform]

        # Call the method
        result: list[str] = Env.get_platform_stack(flags, prefix, suffix)

        # Verify result matches expected
        assert ", ".join(result) == expected


###############################################################################


class TestQuote:
    """Test suite for Env.quote method"""

    @pytest.mark.parametrize(
        "input, type, expected",
        [
            (None, EnvQuoteType.NONE, ""),
            (None, EnvQuoteType.SINGLE, "''"),
            (None, EnvQuoteType.DOUBLE, '""'),
            ("", EnvQuoteType.NONE, ""),
            ("", EnvQuoteType.SINGLE, "''"),
            ("", EnvQuoteType.DOUBLE, '""'),
            (" a \"b'  c   ", EnvQuoteType.NONE, " a \"b'  c   "),
            (" a \"b'  c   ", EnvQuoteType.SINGLE, "' a \"b\\'  c   '"),
            (" a \\\"b\\'  c   ", EnvQuoteType.SINGLE, "' a \\\\\"b\\\\\\'  c   '"),
            (" a \\\"b\\'  c   ", EnvQuoteType.DOUBLE, '" a \\\\\\"b\\\\\'  c   "'),
        ],
    )
    def test_quote(self, input: str, type: str, expected: str):
        # Call the method
        result = Env.quote(input, type)

        # Verify result matches expected
        assert result == expected


###############################################################################


class TestRemoveLineComment:
    """Test suite for Env.remove_line_comment method"""

    @pytest.mark.parametrize(
        "input, expected",
        [
            (None, ""),
            ("", ""),
            ("", ""),
            (" Abc Def  ", " Abc Def  "),
            (" Abc # Def  ", " Abc"),
            (" Abc # Def  \n GH\nIjK", " Abc"),
        ],
    )
    def test_remove_line_comment(self, input: str, expected: tuple[str, str]):

        # Call the method
        result = Env.remove_line_comment(input)

        # Verify result matches expected
        assert result == expected


###############################################################################


class TestUnquote:
    """Test suite for Env.unquote method"""

    @pytest.mark.parametrize(
        "input, expStr, expType",
        [
            (None, "", EnvQuoteType.NONE),
            ("", "", EnvQuoteType.NONE),
            ("abc d", "abc d", EnvQuoteType.NONE),
            ("'abc d'", "abc d", EnvQuoteType.SINGLE),
            ("'abc d\\'", "abc d", EnvQuoteType.SINGLE),
            ('"abc d"', "abc d", EnvQuoteType.DOUBLE),
            ('"abc d\\\\"', "abc d\\", EnvQuoteType.DOUBLE),
            ("'abc' d", "abc", EnvQuoteType.SINGLE),
            ('"abc" d', "abc", EnvQuoteType.DOUBLE),
            ("'abc\\' d", "abc", EnvQuoteType.SINGLE),
            ('"abc\\" d"', 'abc" d', EnvQuoteType.DOUBLE),
        ],
    )
    def test_unquote(self, input: str, expStr: str, expType: EnvQuoteType):
        # Call the method
        result, type = Env.unquote(input)

        # Verify result matches expected
        assert result == expStr
        assert type == expType

    @pytest.mark.parametrize(
        "input",
        [
            ('"abc d'),
            ('"abc d\\"'),
            ("'abc d"),
        ],
    )
    def test_unquote_bad(self, input: str):
        # Call the method

        with pytest.raises(ValueError) as ex:
            Env.unquote(input)

        # Verify result matches expected
        assert "Unterminated" in str(ex.value)


###############################################################################
