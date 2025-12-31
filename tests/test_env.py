#!/usr/bin/env pytest

###############################################################################
# svg2many (C) Alexander Iurovetski 2025
#
# Tests for Cli
###############################################################################

import os
import sys
import pytest

from pytest_mock import MockerFixture

from src.envara.env import Env

###############################################################################


class TestExpandConditionalPatterns:
    """Test suite for Env.__get_var method"""

    @pytest.mark.parametrize("input, env, arg_cnt, args, keep_unknown, expected, exp_prints",
    [
        # ${x-...}

        ("", None, 0, [], False, "", 0),
        ("abc", None, 0, [], False, "abc", 0),
        ("a${1-0}b", None, 0, [], False, "ab", 0),
        ("a${1-0}b", None, 0, [], True, "a${1-0}b", 0),
        ("a${1-0}b", None, 0, [""], False, "ab", 0),
        ("a${1-0}b", None, 0, [""], True, "a${1-0}b", 0),
        ("a${1-0}b", None, 1, [""], False, "ab", 0),
        ("a${1-0}b", None, 0, ["x"], True, "a${1-0}b", 0),
        ("a${1-0}b", None, 1, ["x"], False, "axb", 0),

        # ${x:-...}

        ("a${1:-0}b", None, 0, [], False, "a0b", 0),
        ("a${1:-0}b", None, 0, [], True, "a${1:-0}b", 0),
        ("a${1:-0}b", None, 0, ["x"], False, "a0b", 0),
        ("a${1:-0}b", None, 0, ["x"], True, "a${1:-0}b", 0),
        ("a${1:-0}b", None, 1, ["x"], False, "axb", 0),
        ("a${1:-0}b", None, 1, ["x"], True, "axb", 0),

        # ${x?...}

        ("a${1?Test print}b", None, 0, [], False, "ab", 0),
        ("a${1?Test print}b", None, 0, [], True, "a${1?Test print}b", 1),
        ("a${1?Test print}b", None, 1, ["x"], False, "axb", 0),
        ("a${1?Test print}b", None, 1, ["x"], True, "axb", 0),
        ("a${2?Test print}b", None, 1, ["x"], False, "ab", 0),
        ("a${2?Test print}b", None, 1, ["x"], True, "a${2?Test print}b", 1),
        ("a${bcd?Test print}b", {"a": "bcd"}, 0, [], False, "ab", 0),
        ("a${bcd?Test print}b", {"a": "bcd"}, 0, [], True, "a${bcd?Test print}b", 1),

        # ${x:?...}

        ("a${1:?Test print}b", None, 0, [], False, "ab", 1),
        ("a${1:?Test print}b", None, 0, [], True, "a${1:?Test print}b", 1),
        ("a${1:?Test print}b", None, 1, ["x"], False, "axb", 0),
        ("a${1:?Test print}b", None, 1, ["x"], True, "axb", 0),
        ("a${2:?Test print}b", None, 1, ["x"], False, "ab", 1),
        ("a${2:?Test print}b", None, 1, ["x"], True, "a${2:?Test print}b", 1),
        ("a${bcd:?Test print}b", {"a": "bcd"}, 0, [], False, "ab", 1),
        ("a${bcd:?Test print}b", {"a": "bcd"}, 0, [], True, "a${bcd:?Test print}b", 1),
    ])
    def test_expand_conditional_patterns(
        self, mocker: MockerFixture, input: str, env: dict[str, str], arg_cnt: int,
        args: list[str], keep_unknown: bool, expected: str, exp_prints: int):

        # Arrange
        keys_to_clear = list((env or {}).keys())
        for k, v in (env or {}).items():
            os.environ[k] = v

        mock_print = mocker.patch("builtins.print")

        # Call the method
        result = Env._Env__expand_conditional_patterns(
            input, arg_cnt, args, keep_unknown)

        # Verify result matches expected
        assert result == expected

        # Cleanup
        for k in keys_to_clear:
            os.environ.pop(k, None)

        # Check mocks
        assert mock_print.call_count == exp_prints

        if (exp_prints > 0):
            mock_print.assert_called_with("Test print", file=sys.stderr)

###############################################################################


class TestExpandExplicitPatterns:
    """Test suite for Env.expand_explicit_patterns method"""

    @pytest.mark.parametrize("input, env, arg_cnt, args, keep_unknown, expected",
    [
        ("", None, 0, [], False, ""),
        ("a$1b", None, 1, ["x"], False, "axb"),
        ("a${1}b", None, 1, ["x"], True, "axb"),
        ("a$a${b}", {"a": "efg1"}, 0, [], False, "aefg1"),
        ("a$a${b}", {"a": "efg1"}, 0, [], True, "aefg1${b}"),
        ("a$a$1${b}", {"a": "efg1"}, 1, ["x"], False, "aefg1x"),
        ("a$a${1}${b}", {"a": "efg1"}, 1, ["x"], True, "aefg1x${b}"),
    ])
    def test_expand_explicit_patterns(
        self, input: str, env: dict[str, str], arg_cnt: int, args: list[str],
        keep_unknown: bool, expected: str):

        # Arrange
        keys_to_clear = list((env or {}).keys())
        for k, v in (env or {}).items():
            os.environ[k] = v

        # Call the method
        result = Env._Env__expand_explicit_patterns(
            input, arg_cnt, args, keep_unknown)

        # Verify result matches expected
        assert result == expected

        # Cleanup
        for k in keys_to_clear:
            os.environ.pop(k, None)

###############################################################################


class TestGetArg:
    """Test suite for Env.__get_arg method"""

    @pytest.mark.parametrize("args, index, count, keep_unknown, expected",
    [
        (None, 0, 0, False, ""),
        (None, 0, 0, True, None),
        (None, 0, 1, False, ""),
        (None, 0, 1, True, None),
        ([], 0, 0, False, ""),
        ([], 0, 0, True, None),
        ([], 0, 1, False, ""),
        ([], 0, 1, True, None),
        ([], 2, 1, False, ""),
        ([], 2, 1, True, None),
        (["a1"], 0, 1, False, ""),
        (["a1"], 0, 1, True, None),
        (["a1"], 2, 1, False, ""),
        (["a1"], 2, 1, True, None),
        (["a1"], 1, 1, False, "a1"),
        (["a1"], 1, 1, True, "a1"),
        (["a1", "a2"], 1, 2, False, "a1"),
        (["a1", "a2"], 1, 2, True, "a1"),
        (["a1", "a2"], 2, 2, False, "a2"),
        (["a1", "a2"], 2, 2, True, "a2"),
        (["a1", "a2"], 3, 2, False, ""),
        (["a1", "a2"], 3, 2, True, None),
    ])
    def test_get_arg(
        self, args: list[str] | None, index: int, count: int,
        keep_unknown: bool, expected: str):

        # Call the method
        result = Env._Env__get_arg(args, index, count, keep_unknown)

        # Verify result matches expected
        assert result == expected

###############################################################################


class TestGetVar:
    """Test suite for Env.__get_var method"""

    @pytest.mark.parametrize("env, key, keep_unknown, expected",
    [
        (None, "", False, ("", None)),
        (None, "", True, (None, None)),
        (None, "a", False, ("", None)),
        (None, "a", True, (None, None)),
        ({}, "a", False, ("", None)),
        ({}, "a", True, (None, None)),
        ({"a": "bc"}, "a", False, ("bc", None)),
        ({"a": "bc"}, "a", True, ("bc", None)),
        ({"a": "b", "b": "cd"}, "!a", False, ("cd", "b")),
        ({"a": "b", "b": "cd"}, "!a", True, ("cd", "b")),
        ({"a": "c", "b": "cd"}, "!a", False, ("", "c")),
        ({"a": "c", "b": "cd"}, "!a", True, (None, "c")),
    ])
    def test_get_var(
        self, env: dict[str, str], key: str, keep_unknown: bool,
        expected: tuple[str, str]):

        # Arrange
        keys_to_clear = list((env or {}).keys())
        for k, v in (env or {}).items():
            os.environ[k] = v

        # Call the method
        val, key = Env._Env__get_var(key, keep_unknown)

        # Verify result matches expected
        assert val == expected[0]
        assert key == expected[1]

        # Cleanup
        for k in keys_to_clear:
            os.environ.pop(k, None)

###############################################################################


class TestTryParseInt:
    """Test suite for Env.__try_parse_int method"""

    @pytest.mark.parametrize("input, expected",
    [
        ("", None),
        ("e", None),
        ("1e", None),
        ("e1", None),
        ("1e2", None),
        ("0", 0),
        ("1", 1),
        ("10", 10),
        ("123", 123),
        ("-123", -123),
    ])
    def test_try_parse_int(self, input: str, expected: int | None):
        # Call the method
        result = Env._Env__try_parse_int(input)

        # Verify result matches expected
        assert result == expected


###############################################################################
