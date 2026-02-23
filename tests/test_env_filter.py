#!/usr/bin/env pytest

###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# Tests for EnvFile
###############################################################################

import re

import pytest
from env_filter import EnvFilter

###############################################################################

@pytest.mark.parametrize(
    "input, is_full, expected",
    [
        ('', False, '(?:)'),
        ('', True, '^(?:)$'),
        ('a', False, '(?:a)'),
        ('a', True, '^(?:a)$'),
        ('a,bc,def', False, '(?:a|bc|def)'),
        ('a,bc,def', True, '^(?:a|bc|def)$'),
        ('a[bc]d', False, '(?:a[bc]d)'),
        ('a[bc]d', True, '^(?:a[bc]d)$'),
        ('a[^bc]d', False, '(?:a[^bc]d)'),
        ('a[!bc]d', True, '^(?:a[^bc]d)$'),
        ('ab{c,de}f', False, '(?:ab(?:c|de)f)'),
        ('ab{c,de}f', True, '^(?:ab(?:c|de)f)$'),
        ('a*b{c.c,d*e?}f', False, r'(?:a.*b(?:c\.c|d.*e.)f)'),
        ('a*b{c.c,d*e?}f', True, r'^(?:a.*b(?:c\.c|d.*e.)f)$'),
        ('ab{c,{de,f{g,h*}}f', False, '(?:ab(?:c|(?:de|f(?:g|h.*))f)'),
        ('ab{c,{de,f{g,h*}}f', True, '^(?:ab(?:c|(?:de|f(?:g|h.*))f)$'),
        ('ab{c,{de,f{g,h*}}f', True, '^(?:ab(?:c|(?:de|f(?:g|h.*))f)$'),
        ('dev|test|prod', False, '(?:dev|test|prod)'),
        ('dev|test|prod', True, '(?:dev|test|prod)'),
        # regex-like inputs should be returned unchanged regardless of is_full
        ('(dev|test|prod)', False, '(dev|test|prod)'),
        ('(dev|test|prod)', True, '(dev|test|prod)'),
        ('^abc$', False, '^abc$'),
        ('^abc$', True, '^abc$'),
        ('abc|def', False, '(?:abc|def)'),
        ('abc|def', True, '(?:abc|def)')
    ],
)
def test_limited_glob_str_to_regex_str(input, is_full, expected):
    # direct access to the mangled private static method
    result = EnvFilter._EnvFilter__limited_glob_str_to_regex_str(input, is_full)
    assert result == expected


@pytest.mark.parametrize(
    "indicator, input, check, expected",
    [
        # Most of permutations

        (None, 'a', 'env', True),
        (None, 'a', '.env', True),
        (None, 'a', 'env.', True),
        (None, 'a', '-env', True),
        (None, 'a', 'env-', True),
        (None, 'a', '_env', True),
        (None, 'a', 'env_', True),
        (None, 'a', '.a.env', True),
        (None, 'a', 'a.env', True),
        (None, 'a', 'env.a', True),
        (None, 'a', 'env.a.', True),
        (None, 'a', '.env.a.', True),
        (None, 'a', '..env.a..', True),
        (None, 'a', '..env...a..', True),
        (None, 'a', '_a_env', True),
        (None, 'a', '-_a_env-', True),
        (None, 'a', '._a_env._', True),
        (None, 'a', 'a_env', True),
        (None, 'a', 'a_env_', True),
        (None, 'a', 'env_a', True),
        (None, 'a', '_env_a', True),
        (None, 'a', '_env_a_', True),
        (None, 'a', 'env_a_', True),
        (None, 'a', '_env_a_', True),
        (None, 'a', '__env_a__', True),
        (None, 'a', '__env___a__', True),
        ('', 'a', '.env', False),
        ('', 'a', '__env___a__', True),
        ('', 'a', '__a__', True),

        # Practical

        (None, '{en,fr,jp}?', 'en.x', False),
        (None, '{en,fr,jp}?', 'enu.env-test', True),
        (None, 'en,fr,jp', 'fr.env', True),
        (None, 'en,fr,jp', 'dev_env.en', True),
        (None, 'en,fr,jp', 'prod-env', False),
        (None, 'en,fr', '.env.jp', False),
        (None, 'en,fr', '.jp.env', False),
        (None, 'en,fr', '-jp.env', False),
        (None, 'en,fr', 'jp.env', False),
        ('', 'en,fr', '.env', False),
        ('', 'en,fr', 'env', False),
        ('', 'en,fr', 'en.env', True),
        ('', 'en,fr', 'jp.env', False),
        ('a', 'en,fr', '.env', False),
        ('a', 'en,fr', 'env', False),
        ('a', 'en,fr', '.a', True),
        ('a', 'en,fr', 'a', True),
        ('a', 'en,fr', 'en.a', True),
        ('a', 'en,fr', 'a.en', True),
    ],
)
def test_to_regex(indicator, input, check, expected):
    # direct access to the mangled private static method
    result = EnvFilter.to_regex(indicator, input)
    assert isinstance(result, re.Pattern)
    assert expected == (result.search(check) is not None)
