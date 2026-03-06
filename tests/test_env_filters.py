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
        (["a", "env.bc"], [EnvFilter(None, ["bc"])], ["env.bc"]),
    ],
)
def test_process(input, filters, expected):
    assert EnvFilters.process(input, filters) == expected


###############################################################################
