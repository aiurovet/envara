#!/usr/bin/env python3

###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# An example of how to use the envara package
#
# Run it with 3 arguments like:
#
# python[3] [dir/]example.py v1 23 4
###############################################################################

import os
from pathlib import Path
import sys

# Remove this and the line below if the envara package is installed
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from envara.env_chars import EnvChars
from envara.env import Env
from envara.env_file import EnvFile

###############################################################################


def main():
    """
    Sample program showing the usage of the `envara` library
    """

    # Get the application arguments without the executable (see launch settings)
    args = sys.argv[1:]

    # Make expansions portable betwen POSIX and Windows
    chars = EnvChars.POSIX_WINDOWS if Env.IS_WINDOWS else EnvChars.POSIX
    esc = chars.escape

    # Expand inline and print the result
    input = f"Home ${{HOME:-$USERPROFILE}}, arg {esc}#1: $1 # Line comment"
    print(f"\n*** Expanded string ***\n\n{Env.expand(input, args, chars=chars)}")

    # Define directory that contains all env-like files
    inp_dir = Path("config")

    # List of all platforms
    print(f"\n*** All platforms ***\n")
    print(f'"{'", "'.join(Env.get_all_platforms())}"')

    # List of current platforms
    print(f"\n*** Current platforms ***\n")
    print(f'"{'", "'.join(Env.get_cur_platforms())}"')

    # List files related to the current platform stack
    print(f"\n*** Env file stack ***\n")
    print(f'"{'", "'.join([x.name for x in EnvFile.get_files(inp_dir)])}"')

    # Make a copy of the old environment variables
    old_env = os.environ.copy()

    # Place some env files into directory below
    EnvFile.load(inp_dir, args=args)

    # Show new environment variables
    print(f"\n*** New environment variables ***\n")
    for key, val in os.environ.items():
        if key not in old_env:
            print(f"{key} => {val}")

    return 0


###############################################################################

if __name__ == "__main__":
    exit(main())

###############################################################################
