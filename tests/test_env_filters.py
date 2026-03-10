#!/usr/bin/env pytest

###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# Tests for EnvFile
###############################################################################

import pytest
from envara.env_filter import EnvFilter

from env_filters import EnvFilters

###############################################################################


@pytest.mark.parametrize(
    "input, filters, expected",
    [
        (None, None, None),
        (None, [], None),
        ([], None, []),
        (
            ["a", "bc", "env.bc", "bc_env"],
            [EnvFilter(None, ["bc"])],
            ["bc_env", "env.bc"],
        ),
        (
            ["a", "bc", "bc_env", "env.bc"],
            [EnvFilter(None, ["bc"])],
            ["bc_env", "env.bc"],
        ),
        (
            ["a", "bc", "env.prod", "dev_env"],
            [EnvFilter(None, ["dev", "test", "prod"])],
            ["dev_env", "env.prod"],
        ),
        (
            [
                "a",
                "prod",
                ".env",
                "env-prod.en",
                "env_jp-prod",
                "env.en-prod",
                "env.prod",
                "dev_env",
                ".env.jp.dev",
            ],
            [
                EnvFilter(None, ["prod"], ["dev", "prod"]),
                EnvFilter(None, ["en", "jp"], ["en", "fr", "jp"]),
            ],
            [".env", "env.prod", "env-prod.en", "env.en-prod", "env_jp-prod"],
        ),
        (
            [
                "a",
                "prod",
                ".env",
                "env-prod.en",
                ".env.linux",
                "env_jp-prod",
                "env.en",
                ".env.posix",
                ".env.posix.prod",
                "env.en-prod",
                "env.prod",
                "dev_env",
                ".env.jp.dev",
            ],
            [
                EnvFilter(None, ["posix", "linux"]),
                EnvFilter(None, ["prod"], ["dev", "prod"]),
                EnvFilter(None, ["en"], ["en", "fr", "jp"]),
            ],
            [
                ".env",
                ".env.posix",
                ".env.linux",
                "env.prod",
                ".env.posix.prod",
                "env.en",
                "env-prod.en",
                "env.en-prod",
            ],
        ),
    ],
)
def test_process(input, filters, expected):
    result = EnvFilters.process(input, filters)
    assert result == expected


###############################################################################
