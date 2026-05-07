# envara

© Alexander Iurovetski 2026

A library to expand environment variables, application arguments and escape sequences in arbitrary strings, as well as to load stacked env files, remove line comments, unquote and expand values (if the input was unquoted or enclosed in single quotes), execute sub-commands, and finally extend the environment.

Does not depend on any special Python package.

---

## Table of Contents

- [Sample Usage](#sample-usage)
- [Library Overview](#library-overview)
- [POSIX-style Expansions](#posix-style-expansions)
- [Windows-like Expansions](#windows-like-expansions)
- [Dot-env File Lookup](#dot-env-file-lookup)
- [Which Expansion to Choose?](#which-expansion-to-choose)

---

## Sample Usage

1. Install _envara_ from _PyPI_

2. Create a _.py_ file with the following content, then run it with 3 arbitrary arguments:

```python
###############################################################################
# Run it with 3 arguments like:
#
# python[3] [dir/]example.py v1 23 4
###############################################################################

import os
from pathlib import Path
import sys
from envara.env import Env
from envara.env_file import EnvFile

###############################################################################

def main():
    """
    Sample program showing the usage of the `envara` library
    """

    # Get the application arguments and convert the executable file's path
    # into a simple name: without directory and extension, then replace the
    # 0th argument with that in the command-line arguments
    args = [Path(sys.argv[0]).stem]
    args.extend(sys.argv[1:])

    # Expand inline and print the result
    input: str = r"Home ${HOME:-$USERPROFILE}, arg \#1: $1 # Line comment"
    print(f"\n*** Expanded string ***\n\n{Env.expand(input, args)}")

    # Define directory that contains all env-like files
    inp_dir: Path = Path("config")

    # List of all platforms
    print(f"\n*** All platforms ***\n")
    print(f'"{"\", \"".join(Env.get_all_platforms())}"')

    # List of current platforms
    print(f"\n*** Current platforms ***\n")
    print(f'"{"\", \"".join(Env.get_cur_platforms())}"')

    # List files related to the current platform stack
    print(f"\n*** Env file stack ***\n")
    print(f'"{"\", \"".join([x.name for x in EnvFile.get_files(inp_dir)])}"')

    # Make a copy of the old environment variables
    old_env = os.environ.copy()

    # Place some .env files into directory below
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
```

---

## Library Overview

The _envara_ library provides the following main components:

### `Env` class
Class for string expansions. Provides static methods to:
- Expand environment variables and command-line arguments in strings as well as execute sub-commands
- Unquote strings (remove enclosing quotes)
- Unescape special characters (`\t`, `\n`, `\u0022`, etc.)
- Quote strings with proper escape handling
- Split input string into command-line arguments and apply the actions mentioned above
- Load and process stacked environment files
- Detect and work with multiple platforms (POSIX, Windows, RiscOS, VMS, etc.)

Key class variables:
- `IS_POSIX` - `True` if running under Linux, UNIX, BSD, macOS or similar
- `IS_RISCOS` - `True` if running under Risc OS
- `IS_VMS` - `True` if running under OpenVMS or similar
- `IS_WINDOWS` - `True` if running under Windows or OS/2

### `EnvFile` class
Class for string expansions. Provides static methods to:
- Read series of `key=value` lines from env files
- Remove line comments
- Expand environment variables and arguments
- Expand escaped characters
- Execute sub-commands on POSIX-compliant platforms
- Sets or update those environment variables
- Allows hierarchical OS-specific stacking of such files

### `EnvFilter` and `EnvFilters`
Environment-related filtering, mainly for use with `EnvFile`. Allows filtering env files based on:
- A necessary part of the filename (indicator)
- Current runtime values (e.g., "dev", "prod")
- All possible values for the runtime environment

### Enumerations
- `EnvExpandFlags` - Controls expansion behavior (allow shell commands, subprocess execution, skip hard-quoted strings, strip comments/spaces, unescape, unquote)
- `EnvFileFlags` - Controls file loading behavior (add platforms before/after filters, reset accumulated files)
- `EnvPlatformFlags` - Controls platform listing (add empty string for any platform)
- `EnvQuoteType` - Specifies quote type (none, hard/single-quoted, normal/double-quoted)

---

## POSIX-style Expansions

Implemented via `Env.expand()` which calls private method `_Env__expand_posix()`.

### Supported constructs

**Basic variable expansion:**
- `$NAME` and `${NAME}` - expand variable from the provided mapping (defaults to `os.environ`)
- Positional arguments: `$1`, `$2`, ... (1-based indices supplied via `args`) - out-of-bounds indices leave the pattern unchanged
- `$$` expands to the current process ID

**Length and substrings:**
- `${#NAME}` returns the length of `NAME`'s value
- `${NAME:offset[:length]}` extracts a substring; negative `offset` counts from the end

**Defaulting and alternatives:**
- `${NAME:-word}` - use `word` if `NAME` is unset or null
- `${NAME-word}` - use `word` if `NAME` is unset
- `${NAME:+word}` - use `word` if `NAME` is set and non-empty
- `${NAME:?message}` and `${NAME?message}` - raise `ValueError` with `message` if variable is not set (or null for `:?`)

**Assignment:**
- `${NAME:=word}` - set `NAME` to the expansion of `word` if `NAME` is unset or null
- Assignment writes to the `vars` mapping you pass (if any)

**Pattern removals:**
- `${NAME#pattern}` and `${NAME##pattern}` - remove shortest/longest matching prefix using glob-style patterns
- `${NAME%pattern}` and `${NAME%%pattern}` - remove shortest/longest matching suffix

**Substitution:**
- `${NAME/pat/repl}` - replace first match of glob `pat` with `repl` (replacement is recursively expanded)
- `${NAME//pat/repl}` - replace all matches
- Anchored forms: `${NAME/#pat/repl}` replaces matching prefix, `${NAME/%pat/repl}` replaces matching suffix
- Global anchored forms iteratively apply the anchored substitution

**Case modification (NEW):**
- `${var^}` - uppercase first character
- `${var^^}` - uppercase all characters
- `${var,}` - lowercase first character
- `${var,,}` - lowercase all characters
- `${var~}` - toggle case of first character
- `${var~~}` - toggle case of all characters
- Pattern-based forms: `${var^[pattern]}`, `${var^^[pattern]}`, `${var,[pattern]}`, `${var,,[pattern]}` - apply to characters matching the glob pattern
- When variable is unset, the expression is returned unchanged; when null (empty), the empty string is returned

**Escaping:**
- A backslash before `$` prevents expansion
- Pairs of backslashes reduce appropriately

**Command substitution:**
- `$(...)` and backtick commands are supported
- Inner content is first expanded before execution
- The executed command's stdout (with trailing newline removed) is inserted into the result
- Timeouts and non-zero exit codes raise `ValueError`

### Safety and Configuration

The following parameters control execution of command substitutions:
- `flags`: `EnvExpandFlags` controls expansion
  - `ALLOW_SHELL` - command substitutions executed with `shell=True` (less safe, more flexible)
  - `ALLOW_SUBPROC` - executed with `shell=False` using `shlex.split()` (safer)

## 'Simple' expansions implemented in _Env.expand_ for Windows, OpenVMS, and RiscOS

This method of expansion supports:
- Windows-style `%NAME%`, `%1`, `%*`, `%%`, and simple `%~` modifiers (e.g., `%~dp1`) for extracting path components on Windows-like inputs.
- A substring form for named variables using the syntax `%NAME:~start[,length]%` - negative `start` counts from the end.
- Similarly supports OpenVMS-like variables expansion `'NAME'` as well as RiscOS-like `<NAME>`.

---

## Dot-env File Lookup

The `EnvFile.load()` method looks for the following files. The leading dot is optional; `<sys.platform>` is lowercased; each file is loaded at most once (unless the internal cache is dropped via `EnvFileFlags.RESET_ACCUMULATED`).

**For any filter:**
```
[.-_]env[.-_]
```

**Platforms** (added to the list of filters by default):

| Platform | Files (not limited to) |
|---|---|
| Any platform | `.env`, `-env`, `_env`, `env`, `env-`, `env_`, `.env-`, `.env_`, `-env.`, `-env_`, `_env.`, `_env-` |
| Any POSIX platform | `.env.posix`, `[.]posix.env`, `abc.posix-def_env` (has `env` and `posix` parts) |
| Linux, Android | POSIX + `.env.linux`, `[.]linux.env`, `abc.linux-def_env` |
| BSD-like | POSIX + `.env.bsd`, `[.]bsd.env`, `bsd_abc.def-env.ghi` |
| iOS, iPadOS, macOS | BSD + `.env.darwin`, `[.]darwin.env` |
| Windows | `.env.windows`, `[.]windows.env` |
| VMS | `.env.vms`, `[.]vms.env` |
| Java | POSIX or Windows |

If a platform is not listed explicitly, it falls into the last category. None of these files is required - a file is only loaded if found **and** verified to be relevant to the platform you are running under.

**Extra filters** can also be passed - things like `"dev"` (runtime environment) or `"es"` (current language), as well as lists of all expected environments and languages.

**Example** (portable Chrome launcher):
```
# .env (or .env.any)
APP_NAME = $0
APP_VERSION = "${1}.$2.$3"
APP_FULL_NAME = "$APP_NAME-$APP_VERSION"
PROECT_PATH = ~/Projects/$APP_FULL_NAME
BROWSER_ARGS = "--opt1 arg1 --opt2 arg2"

# .env.linux (or .linux.env)
CMD_CHROME = "google-chrome $BROWSER_ARGS"

# .env.bsd (or bsd.env)
CMD_CHROME = "chrome $BROWSER_ARGS"

# .env.macos (or macos.env)
CMD_CHROME = "\"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome\" $BROWSER_ARGS"

# .env.windows
CMD_CHROME = "chrome $BROWSER_ARGS"
```

---

## Which Expansion to Choose?

By default, the expansion specific to the current platform will be chosen. But you can override that by having the first non-empty line representing a line comment for the desired platform. For instance, if the first non-empty line in a dot-env file starts with `#`, it will force to use POSIX rules. If with `::`, then DOS/Windows rules, if `!`, then OpenVMS, and if `|`, then RiscOS. It is always a good idea to start such file with a meaningful comment anyway, so you can kill two birds with one stone.
---

## Good Luck!

[Back to top](#table-of-contents)
