# envara

© Alexander Iurovetski 2026

A library to expand environment variables, application arguments and escape sequences in arbitrary strings, as well as to load stacked env files, remove line comments, unquote and expand values (if the input was unquoted or enclosed in single quotes), execute sub-commands, and finally extend the environment.

Does not depend on any special Python package.

Please note that version `0.6.1` brought breaking changes: a switch from multiple parameters (for various platform-specific characters) to a single object of the class `EnvCharsData`. It also decides on which platform's rules to use for the variables' expansions in env files based on the first non-empty character(s) representing a start of a line comment. Previously, it was searching for specific patterns in every line. Finally, public methods `Env.expand_posix(...)` and `Env.expand_simple(...)` have been moved to the private scope, so stop using those directly in favour of `Env.expand(...)`.

---

## Table of Contents

- [Sample Usage](#sample-usage)
- [Library Overview](#library-overview)
- [POSIX-style Expansions](#posix-style-expansions)
- [Simple Expansions for Windows and OpenVMS](#simple-expansions-for-windows-and-openvms)
- [Env File Lookup](#env-file-lookup)
- [What Kind of Expansion to Choose in the Env Files?](#what-kind-of-expansion-to-choose-in-the-env-files)
- [Good Luck!](#good-luck)

---

## Sample Usage

1. Install _envara_ from _PyPI_

2. Create a _.py_ file with the following content, then run it with 3 arbitrary arguments:

```python
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
    print('"' + '", "'.join(Env.get_all_platforms()) + '"')

    # List of current platforms
    print(f"\n*** Current platforms ***\n")
    print('"' + '", "'.join(Env.get_cur_platforms()) + '"')

    # List files related to the current platform stack
    print(f"\n*** Env file stack ***\n")
    print('"' + '", "'.join([x.name for x in EnvFile.get_files(inp_dir)]) + '"')

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
```

---

## Library Overview

The _envara_ library provides the following main components:

### `Env` class

Provides string expansions via static methods to:

- Expand environment variables and command-line arguments in strings as well as execute sub-commands
- Unquote strings (remove enclosing quotes)
- Unescape special characters (`\t`, `\n`, `\u0022`, etc.)
- Quote strings with proper escape handling
- Split input string into command-line arguments and apply the actions mentioned above
- Join command-line arguments into a single string escaping all internal spaces
- Load and process stacked environment files
- Detect and work with multiple platforms (POSIX, Windows, VMS, etc.)

Key class variables:

- `IS_POSIX` — `True` if running under Linux, UNIX, BSD/macOS or similar
- `IS_VMS` — `True` if running under OpenVMS or similar
- `IS_WINDOWS` — `True` if running under Windows or OS/2
- `PLATFORM_POSIX` — `"posix"` constant
- `PLATFORM_WINDOWS` — `"windows"` constant
- `PLATFORM_THIS` — `sys.platform.lower()` of the running system
- `SPECIAL` — dict mapping escape-letter keys (`a`, `b`, `f`, `n`, `r`, `t`, `v`) to control characters
- `SYS_PLATFORM_MAP` — regex-to-platform-list mapping driving platform detection

Platform-specific character sets (`EnvChars`):

- `EnvChars.POSIX` — `$` expansion, `\` escape, `'` hard quote, `"` normal quote
- `EnvChars.POSIX_WINDOWS` — Same as `POSIX` but with `^` escape (compatible with Windows paths)
- `EnvChars.WINDOWS` — `%NAME%` expansion, `^` escape, `"` normal quote
- `EnvChars.VMS` — `'NAME'` expansion, `^` escape, `"` normal quote
- `EnvChars.Default` — OS-detected default (auto-initialized at import)
- `EnvChars.Current` — currently active character set (may differ from `Default` after `select()`)

Key methods:

- `EnvChars.init_default()` — (re)initialize `Default` based on the running OS
- `EnvChars.select(based_on)` — choose an `EnvCharsData` variant by matching a line-comment starter against known cutters (`#` for POSIX, `::` for Windows, `!` for VMS)

Each `EnvCharsData` instance also exposes:

- `.copy_with(**overrides)` — create a modified copy (used internally for `POSIX_WINDOWS`)
- `.split_glued()` - split "glued" parts of an argument like pipe or angle brackets without surrounding spaces
- `.expand_len`, `.windup_len`, `.escape_len`, `.cutter_len`, `.hard_quote_len`, `.normal_quote_len` — cached string lengths of each special character
- `.all_quotes` — combined string of normal and hard quote characters

Key static methods:

- `Env.expand(str, ...)` — expand environment variables, arguments, escape sequences, and sub-commands
- `Env.expand_path(path, ...)` — expand a `Path`, with tilde (`~`) home-directory expansion via `Path.expanduser()`
- `Env.strip(str, ...)` — strip leading/trailing spaces and detect surrounding quote type
- `Env.unquote(str, ...)` — remove enclosing quotes (single or double)
- `Env.unescape(str, ...)` — process escape sequences (`\n`, `\t`, `\u0022`, etc.)
- `Env.quote(str, ...)` — enclose in quotes with proper escape handling
- `Env.split(str, ...)` — split into command-line arguments: portable and more advanced than `shlex.split()`
- `Env.join(list, ...)` — join arguments back into a single string, escaping internal spaces rather than enclosing the respective argument in double-quotes (this reflects on Windows treatment of double-quotes passed to the application as normal characters)
- `Env.break_args(list, ...)` — split arguments into proper (app) args and towed (other) args (like pipes, I/O re-directions and logical operators), with a piping indicator
- `Env.escape(str, ...)` — escape whitespace and escape characters in a string (used internally by `join()`)
- `Env.startswith_pipe(list|str|None)` — check whether a string or the first element of a string list represents a pipe (`|`) operator or starts with one, but not with `||`

### `EnvFile` class

Reads series of `key=value` lines from env files, removes line comments, expands environment values and arguments, expands escaped characters, and sets or updates those as environment variables. Also allows hierarchical OS-specific stacking of such files.

Key class constants:

- `EOF_CHAR` — `\x1A` (Ctrl-Z) used as a file separator when concatenating multiple files. Recognized by `load_from_str()` to reset the platform-chars selection for the next file segment.
- `RE_KEY_VALUE` — compiled regex `\s*=\s*` to split each line into key and value.
- `DEFAULT_EXPAND_FLAGS` — default flags for `load()` and `load_from_str()`.

Key public methods:

- `EnvFile.load(dir, indicator, flags, *filters)` — discover and load all relevant env files from a directory, with platform-aware stacking
- `EnvFile.load_from_str(data, args, expand_flags)` — parse a string buffer of `key=value` lines directly, with per-file platform detection via `select_chars()`
- `EnvFile.read_text(files, flags)` — read content from a list of `Path` objects, inserting `EOF_CHAR` separators between files, respecting the loaded-files cache
- `EnvFile.select_chars(input, chars)` — examine the first non-whitespace character(s) of a line to determine which `EnvCharsData` to use by matching cutters (`#` for POSIX, `::` for Windows, `!` for VMS)
- `EnvFile.get_files(dir, indicator, flags, *filters)` — discover eligible env files for a directory with platform-based filtering

### `EnvFilter` and `EnvFilters`

Environment-related filtering, mainly for use with `EnvFile`. Allows filtering env files based on:

- A necessary part of the filename (indicator)
- Current runtime values (e.g., `dev`, `prod`)
- All possible values for the runtime environment

Key methods:

- `EnvFilter(indicator, cur_values, all_values)` — constructor; `cur_values` and `all_values` accept comma-separated strings or lists
- `EnvFilter.has_value(name, value)` — static check whether a value appears as a delimited token within a filename string
- `EnvFilter.search(name)` — find the matching index within `cur_values`/`all_values` for a given filename
- `EnvFilters.process(filenames, filters)` — static method to filter and sort filenames according to a list of `EnvFilter` criteria (called internally by `EnvFile.get_files()`)

### Enumerations

- `EnvExpandFlags` - Controls expansion behavior (allow shell commands, subprocess execution, skip hard-quoted strings, strip comments/spaces, unescape, unquote)
- `EnvFileFlags` - Controls file loading behavior (add platforms before/after filters, reset accumulated files)
- `EnvPlatformFlags` - Controls platform listing (add empty string for any platform)
- `EnvQuoteType` - Specifies quote type (none, hard/single-quoted, normal/double-quoted)

---

## POSIX-style Expansions

In fact, these are bash rules, but it makes sense to apply them to the environment variable expansions on any Linux/BSD/UNIX platform. It is implemented via `Env.expand(...)` which eventually calls private method `__expand_posix(...)`.

### Supported constructs

**Basic variable expansion:**

- `$NAME` and `${NAME}` - expand variable from the provided mapping (defaults to `os.environ`)
- Positional arguments: `$1`, `$2`, … (1-based indices supplied via `args`) - out-of-bounds indices leave the pattern unchanged
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

**Unescaping:**

- An escape character before `$` prevents expansion
- Pairs of backslashes reduce appropriately
- An escape character followed by `xNN` converts into an ASCII character with the hexadecimal code `NN`
- An escape character followed by `uNNNN` converts into a Unicode character with the hexadecimal code `NNNN`
- An escape character followed by `a`, `b`, `f`, `n`, `r`, `t`, `v` is expanded to a bell, back, form-feed,
  newline, carriage-return, horizontal tab, vertical tab
- All other characters, preceded by the escape one, convert to themselves

**Sub-command substitution:**

- `$(...)` and `` `...` `` are supported
- Inner content is first expanded before execution
- The executed sub-command's stdout (with trailing newline removed) is inserted into the result
- Timeouts and non-zero exit codes raise `ValueError`

### Safety and Configuration

The following parameters control execution of command substitutions:

- `flags`: `EnvExpandFlags` controls expansion
- `ALLOW_SHELL` - command substitutions executed with `shell=True` (less safe, more flexible)
- `ALLOW_SUBPROC` - executed with `shell=False` using `shlex.split(...)` (safer)

---

## Simple Expansions for Windows and OpenVMS

This method of expansion supports:

- Windows-style `%NAME%`, `%1`, `%*`, `%%`, and simple `%~` modifiers (e.g., `%~dp1`) for extracting path components on Windows-like inputs.
- A substring form for named variables using the syntax `%NAME:~start[,length]%` - negative `start` counts from the end.
- Even more limited OpenVMS-like variables expansion `'NAME'`

It is implemented via `Env.expand(...)` which eventually calls private method `__expand_simple(...)`.

### POSIX-style on Windows

`EnvChars.POSIX_WINDOWS` provides POSIX-style (`$`-based) expansion with the Windows caret (`^`) as the escape character. This avoids ambiguity between backslash path separators and the POSIX escape character when expanding paths on Windows.

---

## Env File Lookup

The `EnvFile.load(...)` method looks for the following files. The leading dot is optional; `<sys.platform>` is lowercased; each file is loaded at most once (unless the internal cache is dropped via `EnvFileFlags.RESET_ACCUMULATED`).

**For any filter:**

```
[.-_]env[.-_]
```

**Platforms** (added to the list of filters by default):

| Platform           | Files (not limited to)                                                                              |
|--------------------|-----------------------------------------------------------------------------------------------------|
| Any platform       | `.env`, `-env`, `_env`, `env`, `env-`, `env_`, `.env-`, `.env_`, `-env.`, `-env_`, `_env.`, `_env-` |
| Any POSIX platform | `.env.posix`, `[.]posix.env`, `abc.posix-def_env` (have `env` and `posix` parts)                    |
| Linux, Android     | POSIX + `.env.linux`, `[.]linux.env`, `abc.linux-def_env`                                           |
| BSD-like           | POSIX + `.env.bsd`, `[.]bsd.env`, `bsd_abc.def-env.ghi`                                             |
| iOS, iPadOS, macOS | BSD + `.env.darwin`, `[.]darwin.env`                                                                |
| Windows            | `.env.windows`, `[.]windows.env`                                                                    |
| VMS                | `.env.vms`, `[.]vms.env`                                                                            |
| Java               | POSIX or Windows                                                                                    |

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

## What Kind of Expansion to Choose in the Env Files?

By default, the expansion that is specific to the current platform will be chosen. You can override that by having the first non-empty line representing a line comment for the desired platform's rules. For instance, if the first non-empty line in an env file starts with `#`, it will force `Env.expand(...)` to use POSIX (in fact, bash) rules. If it starts with `::`, then Windows, and if with `!`, then OpenVMS will apply. This resembles the shebang `#!` sequence for Linux/BSD/UNIX shell scripts. And it is always a good idea to start such a file with a meaningful comment anyway, so you can address both needs at once.

When multiple files are loaded (via `EnvFile.load()`), the `\x1A` (EOF_CHAR) separator is inserted between them by `read_text()`. When `load_from_str()` encounters this character, it resets the platform-chars selection, allowing each file segment to independently declare its expansion rules via its first comment line.

---

## Good Luck&#33;

[Back to top](#table-of-contents)
