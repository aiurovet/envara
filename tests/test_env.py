#!/usr/bin/env pytest

###############################################################################
# svg2many (C) Alexander Iurovetski 2025
#
# Tests for Cli
###############################################################################

import os
import pytest

from env import Env, EnvExpandFlags, EnvQuoteType

###############################################################################


class TestExpand:
    """Test suite for Env.expand method"""

    @pytest.mark.parametrize("input, env, args, flags, expected",
    [
        ("", {}, [],
         EnvExpandFlags.NONE,
         ""),

        ("a$1b", {}, ["x"],
         EnvExpandFlags.NONE,
         "axb"),

        ("a${1}b", None, ["x"],
         EnvExpandFlags.NONE, "axb"),

        ("a$a${b}", {"a": "efg1"}, [],
         EnvExpandFlags.NONE,
         "aefg1${b}"),

        ("a#$a${b}", {"a": "efg1"}, [],
         EnvExpandFlags.REMOVE_LINE_COMMENT,
         "a"),

        ("a $2 $a #${b}", {"a": "efg1", "b": "xx"}, ["A1", "A2"],
         EnvExpandFlags.REMOVE_LINE_COMMENT |\
         EnvExpandFlags.DECODE_ESCAPED |\
         EnvExpandFlags.REMOVE_QUOTES |
         EnvExpandFlags.SKIP_SINGLE_QUOTED,
         "a A2 efg1"),

        ("'a $2 $a #${b}'", {"a": "efg1", "b": "xx"}, ["A1", "A2"],
         EnvExpandFlags.REMOVE_LINE_COMMENT |\
         EnvExpandFlags.DECODE_ESCAPED |\
         EnvExpandFlags.REMOVE_QUOTES |
         EnvExpandFlags.SKIP_SINGLE_QUOTED,
         "a $2 $a #${b}"),
    ])
    def test_expand(
        self, input: str, env: dict[str, str], args: list[str], flags: EnvExpandFlags,
        expected: str):

        # Arrange
        keys_to_clear = list((env or {}).keys())
        for k, v in (env or {}).items():
            os.environ[k] = v

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

    @pytest.mark.parametrize("input, args, expected",
    [
        (None, [], ""),
        ("", [], ""),
        ("a b c", [], "a b c"),
        ("a$1 b ${2}9", [], "a$1 b ${2}9"),
        ("a$1 b ${2}9", ["A1"], "aA1 b ${2}9"),
        ("a$1 b ${2}9", ["A1", "A2"], "aA1 b A29"),
        ("a$1 b $29", ["A1", "A2"], "aA1 b $29"),
    ])
    def test_expandargs(self, input: str, args: list[str], expected: str):

        # Call the method
        result = Env.expandargs(input, args)

        # Verify result matches expected
        assert result == expected

###############################################################################


class TestRemoveLineComment:
    """Test suite for Env.remove_line_comment method"""

    @pytest.mark.parametrize("input, expected",
    [
        (None, ''),
        ('', ''),
        ('', ''),
        (' Abc Def  ', ' Abc Def  '),
        (' Abc # Def  ', ' Abc'),
        (' Abc # Def  \n GH\nIjK', ' Abc\n GH\nIjK'),
    ])
    def test_remove_line_comment(self, input: str, expected: tuple[str, str]):

        # Call the method
        result = Env.remove_line_comment(input)

        # Verify result matches expected
        assert result == expected

###############################################################################


class TestUnquote:
    """Test suite for Env.unquote method"""

    @pytest.mark.parametrize("input, expStr, expType",
    [
        (None, '', EnvQuoteType.NONE),
        ('', '', EnvQuoteType.NONE),
        ('abc d', 'abc d', EnvQuoteType.NONE),
        ("'abc d'", 'abc d', EnvQuoteType.SINGLE),
        ('"abc d"', 'abc d', EnvQuoteType.DOUBLE),
        ("'abc' d", 'abc', EnvQuoteType.SINGLE),
        ('"abc" d', 'abc', EnvQuoteType.DOUBLE),
        ("'abc\\' d", 'abc\\', EnvQuoteType.SINGLE),
        ('"abc\\" d"', 'abc" d', EnvQuoteType.DOUBLE),
    ])
    def test_unquote(self, input: str, expStr: str, expType: EnvQuoteType):
        # Call the method
        result, type = Env.unquote(input)

        # Verify result matches expected
        assert result == expStr
        assert type == expType

    @pytest.mark.parametrize("input",
    [
        ('"abc d'),
        ("'abc d"),
    ])
    def test_unquote_bad(self, input: str):
        # Call the method

        with pytest.raises(ValueError) as ex:
            Env.unquote(input)

        # Verify result matches expected
        assert "Unterminated" in str(ex.value)


###############################################################################
