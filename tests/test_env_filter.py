#!/usr/bin/env pytest

###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# Tests for EnvFile
###############################################################################

import pytest
from envara.env_filter import EnvFilter

###############################################################################


@pytest.mark.parametrize(
    "input, value, exp_found, exp_equal",
    [
        (None, None, False, False),
        ("", None, False, False),
        (None, "", False, False),
        ("", "", False, False),
        ("ab", "ab", True, True),
        (".ab", ".ab", True, True),
        ("-ab", "ab", True, True),
        ("_ab", "ab", True, True),
        (".ab.", "ab", True, True),
        ("-ab-", "ab", True, True),
        ("_ab_", "ab", True, True),
        (".ab-", "ab", True, True),
        (".ab_", "ab", True, True),
        ("-ab.", "ab", True, True),
        ("-ab_", "ab", True, True),
        ("_ab.", "ab", True, True),
        ("_ab-", "ab", True, True),
        (".abc", "ab", False, False),
        ("-abc", "ab", False, False),
        ("_abc", "ab", False, False),
        ("#abc", "ab", False, False),
        ("#abc.", "ab", False, False),
        ("#abc-", "ab", False, False),
        ("#abc_", "ab", False, False),
        ("ab", "abc", False, False),
        ("abc", "ab", False, False),
        ("abc.ab", "ab", True, False),
        ("abc-ab_d", "ab", True, False),
        (".abc-ab_d", "ab", True, False),
        ("abc", "bc", False, False),
        ("ab.c", "ab", True, False),
        ("ab-c", "ab", True, False),
        ("ab_c", "ab", True, False),
        ("a.bc", "bc", True, False),
        ("a-bc", "bc", True, False),
        ("a_bc", "bc", True, False),
        ("a.bc.def", "bc", True, False),
        ("a.bc-def", "bc", True, False),
        ("a.bc_def", "bc", True, False),
        ("a-bc.def", "bc", True, False),
        ("a-bc-def", "bc", True, False),
        ("a-bc_def", "bc", True, False),
        ("a_bc.def", "bc", True, False),
        ("a_bc-def", "bc", True, False),
        ("a_bc_def", "bc", True, False),
        ("a.bc#def", "bc", False, False),
        ("a-bc#def", "bc", False, False),
        ("a#_bc#def", "bc", False, False),
        ("a#bc.def", "bc", False, False),
        ("a#bc-def", "bc", False, False),
        ("a#bc_def", "bc", False, False),
    ],
)
def test_has_value(input, value, exp_found, exp_equal):
    # Arrange
    is_found, are_equal = EnvFilter.has_value(input, value)
    assert is_found == exp_found
    assert are_equal == exp_equal


@pytest.mark.parametrize(
    "input, indicator, cur_values, all_values, expected",
    [
        ("", None, None, None, -1),
        ("", "", None, None, -1),
        ("", None, [], [], -1),
        (".env", None, [], [], 0),
        ("-env", None, [], [], 0),
        ("_env", None, [], [], 0),
        ("env", None, [], [], 0),
        ("env-", None, [], [], 0),
        ("env_", None, [], [], 0),
        (".ab", "ab", [], [], 0),
        ("-ab", "ab", [], [], 0),
        ("_ab", "ab", [], [], 0),
        ("ab", "ab", [], [], 0),
        ("ab-", "ab", [], [], 0),
        ("ab_", "ab", [], [], 0),
        (".env", None, ["dev"], ["dev", "test", "prod"], 0),
        ("-env", None, ["dev"], ["dev", "test", "prod"], 0),
        ("_env", None, ["dev"], ["dev", "test", "prod"], 0),
        ("env", None, ["dev"], ["dev", "test", "prod"], 0),
        ("env-", None, ["dev"], ["dev", "test", "prod"], 0),
        ("env_", None, ["dev"], ["dev", "test", "prod"], 0),
        (".env.dev", None, ["dev", "test", "prod"], None, 1),
        ("dev.env", None, ["dev", "test", "prod"], None, 1),
        (".env-test", None, ["dev", "test", "prod"], None, 2),
        ("test_env", None, ["dev", "test", "prod"], None, 2),
        ("fr.prod.env", None, ["dev", "test", "prod"], None, 3),
        ("fr.prod2.env", None, ["dev", "test", "prod"], None, 0),
        ("fr.prod.env", None, ["dev"], ["dev", "test", "prod"], -1),
    ],
)
def test_search(input, indicator, cur_values, all_values, expected):
    # Arrange
    filter = EnvFilter(indicator, cur_values, all_values)

    # direct access to the mangled private static method
    result = filter.search(input)
    assert result == expected
