#!/usr/bin/env python3

###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# How to use the envara package
###############################################################################

import os
from pathlib import Path
import sys
from envara.env import Env
from envara.env_file import EnvFile


def main():
    """
    Sample program showing the usage of the `envara` library
    """

    # Expand inline and print the result
    input: str = r"Home ${HOME:-$USERPROFILE}, arg \#1: $1 # Line comment"
    print(f"\n*** Expanded string ***\n\n{Env.expand(input, sys.argv)}")

    # Make a copy of the old environment variables
    old_env = os.environ.copy()

    # Place some .env files into directory below
    EnvFile.load(dir=Path("config"), args=sys.argv)

    # Show new environment variables
    print(f"\n*** New environment variables ***\n")
    for key, val in os.environ.items():
        if key not in old_env:
            print(f"{key} => {val}")

    return 0


if __name__ == "__main__":
    exit(main())
