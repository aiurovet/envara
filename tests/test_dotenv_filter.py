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
    "input, check, expected",
    [
        # Minimal: no extra filters

        ('', '', False),
        ('', 'a', False),
        ('', '.env', True),
        ('', '-env', True),
        ('', '_env', True),
        ('', 'env_', False),
        ('', 'env.', False),
        ('', 'env-', False),
        ('', 'env_', False),
        ('', '.env.', False),
        ('', '-env-', False),
        ('', '_env_', False),
        ('', '.env-', False),
        ('', '-env_', False),
        ('', '_env-', False),
        ('', '._env-', False),
        ('', '_env-_', False),
        ('', '..env..', False),
        ('', '..env', True),
        ('', '--env', True),
        ('', '__env', True),

        # Close to minimal

        ('a', 'env', False),
        ('a', '.env', False),
        ('a', '-env', False),
        ('a', '_env', False),

        ('a', 'ax', False),
        ('a', 'a.x', True),
        ('a', 'a-x', True),
        ('a', 'a_x', True),

        ('a', '.x.a', True),
        ('a', '.x-a', True),
        ('a', '.x_a', True),
        ('a', '-x.a', True),
        ('a', '-x-a', True),
        ('a', '-x_a', True),

        ('{en,fr,jp}?', 'en.x', False),
        ('{en,fr,jp}?', 'enu.env-test', True),
        ('en,fr,jp', 'fr.env', True),
        ('en,fr,jp', 'dev_env.en', True),
        ('en,fr,jp', 'prod-env', False),
        ('en,fr', '.env.jp', False),
        ('en,fr', '.jp.env', False),
        ('en,fr', '-jp.env', False),
        ('en,fr', 'jp.env', False),
    ],
)
def test_to_regex(input, check, expected):
    # direct access to the mangled private static method
    result = DotEnvFilter.to_regex(input)
    assert isinstance(result, re.Pattern)
    assert expected == (result.search(check) is not None)
