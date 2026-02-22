#!/usr/bin/env pytest

###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# Tests for DotEnv
###############################################################################

import re

import pytest
from envara.dotenv_filter import DotEnvFilter

###############################################################################

@pytest.mark.parametrize(
    "input, is_full, expected",
    [
        ('', False, '()'),
        ('', True, '^()$'),
        ('a', False, '(a)'),
        ('a', True, '^(a)$'),
        ('a,bc,def', False, '(a|bc|def)'),
        ('a,bc,def', True, '^(a|bc|def)$'),
        ('ab{c,de}f', False, '(ab(c|de)f)'),
        ('ab{c,de}f', True, '^(ab(c|de)f)$'),
        ('a*b{c.c,d*e?}f', False, r'(a.*b(c\.c|d.*e.)f)'),
        ('a*b{c.c,d*e?}f', True, r'^(a.*b(c\.c|d.*e.)f)$'),
        ('ab{c,{de,f{g,h*}}f', False, '(ab(c|(de|f(g|h.*))f)'),
        ('ab{c,{de,f{g,h*}}f', True, '^(ab(c|(de|f(g|h.*))f)$'),
        ('ab{c,{de,f{g,h*}}f', True, '^(ab(c|(de|f(g|h.*))f)$')
    ],
)
def test_limited_glob_str_to_regex_str(input, is_full, expected):
    # direct access to the mangled private static method
    result = DotEnvFilter._DotEnvFilter__limited_glob_str_to_regex_str(input, is_full)
    assert result == expected


@pytest.mark.parametrize(
    "source, indicator, check, expected",
    [
        # Most of permutations

        ('a', None, 'env', True),
        ('a', None, '.env', True),
        ('a', None, 'env.', True),
        ('a', None, '-env', True),
        ('a', None, 'env-', True),
        ('a', None, '_env', True),
        ('a', None, 'env_', True),
        ('a', None, '.a.env', True),
        ('a', None, 'a.env', True),
        ('a', None, 'env.a', True),
        ('a', None, 'env.a.', True),
        ('a', None, '.env.a.', True),
        ('a', None, '..env.a..', True),
        ('a', None, '..env...a..', True),
        ('a', None, '_a_env', True),
        ('a', None, '-_a_env-', True),
        ('a', None, '._a_env._', True),
        ('a', None, 'a_env', True),
        ('a', None, 'a_env_', True),
        ('a', None, 'env_a', True),
        ('a', None, '_env_a', True),
        ('a', None, '_env_a_', True),
        ('a', None, 'env_a_', True),
        ('a', None, '_env_a_', True),
        ('a', None, '__env_a__', True),
        ('a', None, '__env___a__', True),
        ('a', '', '.env', False),
        ('a', '', '__env___a__', True),
        ('a', '', '__a__', True),

        # Practical

        ('{en,fr,jp}?', None, 'en.x', False),
        ('{en,fr,jp}?', None, 'enu.env-test', True),
        ('en,fr,jp', None, 'fr.env', True),
        ('en,fr,jp', None, 'dev_env.en', True),
        ('en,fr,jp', None, 'prod-env', False),
        ('en,fr', None, '.env.jp', False),
        ('en,fr', None, '.jp.env', False),
        ('en,fr', None, '-jp.env', False),
        ('en,fr', None, 'jp.env', False),
        ('en,fr', '', '.env', False),
        ('en,fr', '', 'env', False),
        ('en,fr', '', 'en.env', True),
        ('en,fr', '', 'jp.env', False),
        ('en,fr', 'a', '.env', False),
        ('en,fr', 'a', 'env', False),
        ('en,fr', 'a', '.a', True),
        ('en,fr', 'a', 'a', True),
        ('en,fr', 'a', 'en.a', True),
        ('en,fr', 'a', 'a.en', True),
    ],
)
def test_to_regex(source, indicator, check, expected):
    # direct access to the mangled private static method
    result = DotEnvFilter.to_regex(source, ind=indicator)
    assert isinstance(result, re.Pattern)
    assert expected == (result.search(check) is not None)
