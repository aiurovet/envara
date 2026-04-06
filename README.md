# envara

© Alexander Iurovetski 2026

A library to expand environment variables, application arguments and escape sequences in arbitrary strings, as well as to load stacked env files, remove line comments, unquote and expand values (if the input was unquoted or enclosed in single quotes), execute sub-commands, and finally extend the environment.

Does not depend on any special Python package.

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

## class `Env`

Class for string expansions.

### Class Variables

| Name | Type | Description |
|---|---|---|
| `IS_POSIX` | `bool` | `True` if the app is running under Linux, UNIX, BSD, macOS or similar |
| `IS_RISCOS` | `bool` | `True` if the app is running under Risc OS |
| `IS_VMS` | `bool` | `True` if the app is running under OpenVMS or similar |
| `IS_WINDOWS` | `bool` | `True` if the app is running under Windows or OS/2 |
| `PLATFORM_POSIX` | `str` | A text indicating a POSIX-compatible platform |
| `PLATFORM_WINDOWS` | `str` | A text indicating a Windows-compatible platform |
| `PLATFORM_THIS` | `str` | A text indicating the running platform |
| `SPECIAL` | `dict[str, str]` | Rules on how to convert special characters when they follow an odd number of escape characters |
| `SYS_PLATFORM_MAP` | `dict[str, list[str]]` | Rules (regex_str => list_of_str) on how to stack platforms from common to specific |

---

### `Env.expand()`

> `Path | str`

Unquote the input if required via flags, remove trailing line comment if
required via flags, expand the result with the arguments if required via flags,
expand the result with the environment variables' values. The method follows
POSIX and DOS/Windows expansion conventions depending on what was found first:
dollar or percent, then backslash or caret (obviously, the POSIX style is by far
more advanced).

```python
@staticmethod
def expand(
    input: Path | str,
    args: list[str] | None = None,
    flags: EnvExpandFlags = EnvExpandFlags.DEFAULT,
    strip_spaces: bool = True,
    escape_chars: str = None,
    expand_chars: str = None,
    cutter_chars: str = None,
    hard_quotes: str = None,
    info: EnvParseInfo | None = None,
) -> Path | str: ...
```

**Parameters**

| Name | Type | Description |
|---|---|---|
| `input` | `str` | Path or string to expand |
| `args` | `list[str] \| None` | List of arguments to expand `$#`, `$1`, `$2`, … |
| `flags` | `EnvExpandFlags \| None` | Flags controlling what/how to expand input |
| `strip_spaces` | `bool` | `True` if can remove spaces from the start and end of `input` |
| `escape_chars` | `str` | Character(s) treated as candidates for escaping; whichever comes first in the input will be considered |
| `expand_chars` | `str` | Character(s) treated as candidates for expanding environment variables when found non-escaped; whichever comes first will be considered |
| `windup_chars` | `str` | Character(s) treated as candidates for closing the environment variable placeholder (e.g. `>` for RiscOS) |
| `cutter_chars` | `str` | Character(s) treated as candidates for the end of data in a string (i.e. beginning of a line comment) when found non-escaped and outside a quoted sub-string; whichever comes first will be considered |
| `hard_quotes` | `str` | String containing all quote characters that require escaping to be ignored (e.g. a single quote) |
| `out_info` | `EnvParseInfo \| None` | If you need the details of how the string was parsed, or to enforce those, set this argument to an instance of `EnvParseInfo` |

**Returns** — Expanded Path object or string.

---

### `Env.expand_posix()`

This code was mainly generated using Copilot

> `str`

Expand environment variables and sub-processes according to complex POSIX rules:
like `${ABC:-${DEF:-$(uname -a)}}`. See the description of arguments under the
main method `expand(...)`.

```python
@staticmethod
def expand_posix(
    input: Path | str,
    args: list[str] | None = None,
    vars: dict[str, str] | None = os.environ,
    expand_char: str = EnvParseInfo.POSIX_EXPAND_CHAR,
    escape_char: str = EnvParseInfo.POSIX_ESCAPE_CHAR,
    expand_flags: EnvExpandFlags = EnvExpandFlags.DEFAULT,
    subprocess_timeout: float | None = None,
) -> Path | str: ...
```

**Returns** — Expanded Path object or string.

---

### `Env.expand_simple()`

This code was mainly generated using Copilot

> `str`

Expand environment variables and sub-processes according to simple rules and
symmetric expand characters: like `%ABC%` in Windows or `<ABC>` in RiscOS.
See the description of arguments under the main method `expand(...)`.

```python
@staticmethod
def expand_simple(
    input: Path | str,
    args: list[str] | None = None,
    vars: dict[str, str] | None = None,
    expand_char: str = EnvParseInfo.WINDOWS_EXPAND_CHAR,
    windup_char: str | None = None,
    escape_char: str = EnvParseInfo.WINDOWS_ESCAPE_CHAR,
) -> str: ...
```

**Returns** — Expanded Path pbject or string.

---

### `Env.get_all_platforms()`

> `list[str]`

Get the list of all supported platforms (see `Env.SYS_PLATFORM_MAP`).

```python
@staticmethod
def get_all_platforms(
    flags: EnvPlatformFlags = EnvPlatformFlags.NONE,
) -> list[str]: ...
```

**Parameters**

| Name | Type | Description |
|---|---|---|
| `flags` | `EnvPlatformFlags` | Controls which items will be added to the stack |

**Returns** — List of all relevant platforms.

---

### `Env.get_cur_platforms()`

> `list[str]`

Get the list of platforms from more generic to more specific ones. For instance,
if an application is running on Linux, it could be `["posix", "linux",
Env.PLATFORM_THIS]`, or for macOS it could be `["posix", "bsd", "darwin",
"macos", Env.PLATFORM_THIS]`. The last item will be added only if more specific
than `"macOS"`. An empty string is added first to the returned list if you set
the `EnvPlatformFlags.ADD_EMPTY` bit in `flags`.

```python
@staticmethod
def get_cur_platforms(
    flags: EnvPlatformFlags = EnvPlatformFlags.NONE,
) -> list[str]: ...
```

**Parameters**

| Name | Type | Description |
|---|---|---|
| `flags` | `EnvPlatformFlags` | Controls which items will be added to the list |

**Returns** — List of all relevant platforms.

---

### `Env.quote()`

> `str`

Enclose `input` in quotes. Neither leading, nor trailing whitespaces are removed
before checking the leading quotes. Use `.strip()` yourself before calling this
method if needed.

```python
@staticmethod
def quote(
    input: str,
    type: EnvQuoteType = EnvQuoteType.DOUBLE,
    escape_char: str = None,
) -> str: ...
```

**Parameters**

| Name | Type | Description |
|---|---|---|
| `input` | `str` | String being expanded |
| `type` | `EnvQuoteType` | Type of quotes to enclose in |
| `escape_char` | `str` | Escape character to use |

**Returns** — Quoted string with possible quotes and escape characters from the inside being escaped.

---

### `Env.unescape()`

> `str`

Unescape `\t`, `\n`, `\u0022` etc.

```python
@staticmethod
def unescape(
    input: str,
    escape_char: str = None,
    strip_blanks: bool = False,
) -> str: ...
```

**Parameters**

| Name | Type | Description |
|---|---|---|
| `input` | `str` | Input string to unescape escaped characters in |
| `escape_char` | `str` | String to be treated as escape character |
| `strip_blanks` | `bool` | `True` = remove leading and trailing blanks |

**Returns** — Unescaped string, optionally stripped of blanks.

---

### `Env.unquote()`

> `tuple[str, EnvParseInfo]`

Remove enclosing quotes from a string, ignoring everything beyond the closing
quote and ignoring escaped quotes. Raises `ValueError` if a dangling escape or
no closing quote is found.

In most cases you'd rather use `Env.expand()` that calls this method, then
expands environment variables, arguments, and unescapes special characters.

```python
@staticmethod
def unquote(
    input: str,
    strip_spaces: bool = True,
    escape_chars: str = None,
    expand_chars: str = None,
    cutter_chars: str = None,
    hard_quotes: str = None,
) -> tuple[str, EnvParseInfo]: ...
```

**Parameters**

| Name | Type | Description |
|---|---|---|
| `input` | `str` | String to remove enclosing quotes from |
| `strip_spaces` | `bool` | `True` if should strip leading and trailing spaces (if quoted, don't strip again after unquoting) |
| `escape_chars` | `str` | Character(s) treated as candidates for escaping; whichever comes first in the input will be returned in `.escape_char` |
| `expand_chars` | `str` | Character(s) treated as candidates for expanding environment variables when found non-escaped; whichever comes first is returned in `.expand_char` |
| `cutter_chars` | `str` | Character(s) treated as candidates for the end of data in a string (i.e. beginning of a line comment) when found non-escaped and outside a quoted sub-string; whichever comes first is returned in `.cutter_char` |
| `hard_quotes` | `str` | String containing all quote characters that require escaping to be ignored (e.g. a single quote) |

**Returns** — Unquoted input and details (see `EnvParseInfo`).

---

## class `EnvFile`

Reads series of `key=value` lines from env files, removes line comments,
expands environment values and arguments, expands escaped characters, and sets
or updates those as environment variables. Also allows hierarchical
OS-specific stacking of such files.

### Class Variables

| Name | Type | Description |
|---|---|---|
| `DEFAULT_EXPAND_FLAGS` | `EnvExpandFlags` | Default set of string expansion flags |
| `RE_KEY_VALUE` | `re.Pattern` | Regex to split a string into key and value |

---

### `EnvFile.get_files()`

> `list[Path]`

Get list of eligible env files. Adds a list of platform names if `flags` includes `EnvFileFlags.ADD_PLATFORMS_BEFORE` (default) or `EnvFileFlags.ADD_PLATFORMS_AFTER`.

```python
@staticmethod
def get_files(
    dir: Path | None = None,
    indicator: str | None = None,
    flags: EnvFileFlags = EnvFileFlags.ADD_PLATFORMS_BEFORE,
    *filters: list[EnvFilter] | EnvFilter,
) -> list[Path]: ...
```

**Parameters**

| Name | Type | Description |
|---|---|---|
| `dir` | `Path \| None` | Directory to look in |
| `indicator` | `str \| None` | Necessary part of every relevant filename |
| `flags` | `EnvFileFlags` | Add platform names to filters (default: `EnvFileFlags.ADD_PLATFORMS_BEFORE`) |
| `*filters` | `EnvFilter` | One or more `EnvFilter` objects specifying current value(s) and all possibilities |

**Returns** — List of matching paths in the given directory, sorted in the order of filters.

---

### `EnvFile.load()`

Add key/expanded-value pairs from `.env`-compliant file(s) to `os.environ`.

```python
@staticmethod
def load(
    dir: Path | None = None,
    indicator: str = EnvFilter.DEFAULT_INDICATOR,
    file_flags: EnvFileFlags = EnvFileFlags.ADD_PLATFORMS_BEFORE,
    args: list[str] | None = None,
    expand_flags: EnvExpandFlags = DEFAULT_EXPAND_FLAGS,
    *filters: list[str] | str | None,
): ...
```

**Parameters**

| Name | Type | Description |
|---|---|---|
| `dir` | `Path \| str \| None` | Default directory to locate platform-specific files |
| `indicator` | `str` | Necessary part of every relevant filename, default: `EnvFilter.DEFAULT_INDICATOR` |
| `file_flags` | `EnvFileFlags` | Describes what and how to load |
| `args` | `list[str] \| None` | List of arguments (e.g. application args) to expand placeholders like `$1`, `${2}`, … |
| `expand_flags` | `EnvExpandFlags` | Describes how to expand env vars and app args |
| `*filters` | `EnvFilter` | One or more `EnvFilter` objects specifying current value(s) and all possibilities |

---

### `EnvFile.load_from_str()`

Add key/expanded-value pairs from a string buffer to `os.environ`.

```python
@staticmethod
def load_from_str(
    data: str | None,
    args: list[str] | None = None,
    expand_flags: EnvExpandFlags = DEFAULT_EXPAND_FLAGS,
): ...
```

**Parameters**

| Name | Type | Description |
|---|---|---|
| `data` | `str` | String to parse, then load env variables from |
| `args` | `list[str] \| None` | List of arguments (e.g. application args) to expand placeholders like `$1`, `${2}`, … |
| `expand_flags` | `EnvExpandFlags` | Describes how to expand env vars and app args |

---

### `EnvFile.read_text()`

> `str`

Load the content of all files as text and return. May discard previously loaded
content if `EnvFileFlags.RESET_ACCUMULATED` is set.

```python
@staticmethod
def read_text(
    files: list[Path],
    flags: EnvFileFlags = EnvFileFlags.ADD_PLATFORMS_BEFORE,
) -> str: ...
```

**Parameters**

| Name | Type | Description |
|---|---|---|
| `files` | `list[Path]` | List of `Path` objects to read text from |
| `flags` | `EnvFileFlags` | Describes what and how to load |

**Returns** — Concatenated file contents separated by newlines.

---

## class `EnvFilter`

Environment-related filtering, mainly for use with `EnvFile`.

### Class Variables

| Name | Type | Description |
|---|---|---|
| `DEFAULT_RE_FLAGS` | `re.RegexFlag` | Default regex flags to compile with |
| `DEFAULT_INDICATOR` | `str` | Default env file type without leading extension separator (`"env"`) |
| `DEFAULT_STRIP_RE` | `re.Pattern` | Regex to strip all unnecessary blanks around every delimited field |

---

### `EnvFilter.__init__()`

Constructor.

```python
def __init__(
    self,
    indicator: str = DEFAULT_INDICATOR,
    cur_values: list[str] | str | None = None,
    all_values: list[str] | str | None = None,
): ...
```

**Parameters / Properties**

| Name | Type | Description |
|---|---|---|
| `indicator` | `str \| None` | A necessary part of a name (always present), default: `DEFAULT_INDICATOR` |
| `cur_values` | `list[str] \| None` | One or more strings relevant to the current run |
| `all_values` | `list[str] \| None` | All possible values |

---

### `EnvFilter.has_value()`

> `bool`

Check the input contains the given value separated from the rest by a dot,
dash and/or underscore as well as being at the start start or at the end of
the input. While `has_value("abc", "ab")` returns `False`, separation at
both sides works: `has_value("ab.c", "ab")`, `has_value("c_ab", "ab")`, as
well as `has_value("c-ab_c", "ab")` all return `True`. Essentially, this is
a limited version of a word match

```python
def has_value(
    self,
    input: str | None,
    value: str | None,
) -> bool: ...
```

**Parameters**

| Name | Type | Description |
|---|---|---|
| `input` | `str \| None` | String to search value for |
| `value` | `str \| None` | String to search in the input |

**Returns** — `True` if the input matches, `False` otherwise.

---

### `EnvFilter.search()`

> `int`

Find matching item no for the input string. Requirements:

- the indicator should be found if non-empty
- either one of the current values should be found or none of
  all values (i.e.'any'): assuming runtime environments include
  `dev`, `test` and `prod`, then `.env`, `.env.en.prod`,
  `fr-prod.env` and `prod_jp_env` should be found, but neither
  `.env.dev`, `.env.dev.en`, nor `en_test.env`, nor `test-env`

```python
def search(
    self,
    input: list[str] | str | None,
) -> bool: ...
```

**Parameters**

| Name | Type | Description |
|---|---|---|
| `self` | | The object |
| `input` | `str \| None` | The string to match against current and all values |
| `value` | `str \| None` | String to search in the input |

**Returns** — index in `cur_values` if found; otherwise, 0 if not found in
`all_values` (i.e. applies to all), or -1 if found (i.e. should filter out)

---

## class `EnvFilters`

Helpers for `EnvFilter`.

---

### `EnvFilters.process()`

Filter and sort the input list of strings according to filters, and in the
order those passed. In a highly unlikely event of no difference found, a
mere case-sensitive string comparison engaged.

```python
def process(
    input: list[str],
    filters: list[EnvFilter],
): ...
```

**Parameters**

| Name | Type | Description |
|---|---|---|
| `indicator` | `str \| None` | A necessary part of a name (always present), default: `DEFAULT_INDICATOR` |
| `cur_values` | `list[str] \| None` | One or more strings relevant to the current run |
| `filters` | `list[EnvFilter] \| None` | List of filters to check against |

**Returns** — input list filtered and sorted according to filters

---

## class `EnvParseInfo`

Details of what was found in a string while removing quotes, as well as the
original string and the result of its unquoting.

### Class Variables

| Name | Type | Value | Description |
|---|---|---|---|
| `POSIX_CUTTER_CHAR` | `str` | `"#"` | POSIX line comment character |
| `POSIX_EXPAND_CHAR` | `str` | `"$"` | POSIX variable expansion character |
| `POSIX_ESCAPE_CHAR` | `str` | `"\\"` | POSIX escape character |
| `RISCOS_CUTTER_CHAR` | `str` | `"\|"` | VMS line comment character |
| `RISCOS_EXPAND_CHAR` | `str` | `"<"` | RiscOS variable expansion character |
| `RISCOS_WINDUP_CHAR` | `str` | `">"` | RiscOS variable windup character |
| `RISCOS_ESCAPE_CHAR` | `str` | `"\\"` | VMS escape character |
| `VMS_CUTTER_CHAR` | `str` | `"!"` | VMS line comment character |
| `VMS_EXPAND_CHAR` | `str` | `"'"` | VMS variable expansion character |
| `VMS_ESCAPE_CHAR` | `str` | `"^"` | VMS escape character |
| `WINDOWS_CUTTER_CHAR` | `str` | `""` | Windows/DOS line comment character (absent) |
| `WINDOWS_EXPAND_CHAR` | `str` | `"%"` | Windows/DOS variable expansion character |
| `WINDOWS_ESCAPE_CHAR` | `str` | `"^"` | Windows/DOS escape character |

---

### `EnvParseInfo.__init__()`

Constructor.

```python
def __init__(
    self,
    input: str | None = None,
    result: str | None = None,
    expand_char: str | None = None,
    windup_char: str | None = None,
    escape_char: str | None = None,
    cutter_char: str | None = None,
    quote_type: EnvQuoteType = EnvQuoteType.NONE,
): ...
```

**Parameters / Properties**

| Name | Type | Description |
|---|---|---|
| `input` | `str` | String being unquoted |
| `result` | `str` | Result of unquoting |
| `expand_char` | `str` | First non-escaped and non-quoted expand character encountered: dollar, percent, angle bracket |
| `windup_char` | `str` | Character that acts as the end of an environment variable token in non-POSIX OSes (normally, the same as expand_char, but sometimes, might differ, like for RiscOS) |
| `escape_char` | `str` | First non-escaped and non-quoted escape character encountered: backslash, backtick, caret |
| `cutter_char` | `str` | First non-escaped and non-quoted character recognised as the end of data in a string (like a line comment start): hash |
| `quote_type` | `EnvQuoteType` | Type of enclosing quotes found |

---

### `EnvParseInfo.copy_to()`

Constructor.

```python
def copy_to(
    self,
    to
): ...
```

**Parameters**

| Name | Type | Description |
|---|---|---|
| `self` | | The object (source) |
| `to` | | Destination object |

---

### `EnvParseInfo.get_default_cutter_char()`

> `str`

Get the platform-specific default cutter character.

```python
@staticmethod
def get_default_cutter_char() -> str: ...
```

**Returns** — Default cutter character: `#` on POSIX, `` on Windows, `!` on VMS, `|` on RiscOS.

---

### `EnvParseInfo.get_default_escape_char()`

> `str`

Get the platform-specific default escape character.

```python
@staticmethod
def get_default_escape_char() -> str: ...
```

**Returns** — Default escape character: `\` on POSIX/RiscOS, `^` on Windows/VMS.

---

### `EnvParseInfo.get_default_expand_char()`

> `str`

Get the platform-specific default expand character.

```python
@staticmethod
def get_default_expand_char() -> str: ...
```

**Returns** — Default expand character: `$` on POSIX, `%` on Windows, `'` on VMS, `<` on RiscOS.

---

### `EnvParseInfo.get_default_windup_char()`

> `str`

Get the platform-specific default windup character that is used to close the environment variable expansion.

```python
@staticmethod
def get_default_windup_char() -> str: ...
```

**Returns** — Default windup character: `>` on RiscOS, otherwise the default expand character.

---

## class `EnvExpandFlags`

`IntFlag` enumeration controlling the behaviour of `Env.expand(...)`.

| Member | Value | Description |
|---|---|---|
| `NONE` | `0` | No flag set |
| `ALLOW_SHELL` | `1 << 0` | Execute raw shell commands like `$(...)` or `` `...` `` — `expand_posix()` only |
| `ALLOW_SUBPROC` | `1 << 1` | Parse shell commands like `$(...)` or `` `...` `` and execute — `expand_posix()` only |
| `REMOVE_LINE_COMMENT` | `1 << 2` | Remove hash `#` (outside the quotes if found) and everything beyond that |
| `REMOVE_QUOTES` | `1 << 3` | Remove leading and trailing quote; don't expand single-quoted strings |
| `SKIP_ENV_VARS` | `1 << 4` | Do not expand environment variables |
| `SKIP_SINGLE_QUOTED` | `1 << 5` | If a string is embraced in apostrophes, don't expand it |
| `UNESCAPE` | `1 << 6` | Expand escaped characters, including characters represented by hexadecimal or unicode sequences |
| `DEFAULT` | `ALLOW_SHELL \| REMOVE_QUOTES \| SKIP_SINGLE_QUOTED \| UNESCAPE` | Default set of flags |

---

## class `EnvFileFlags`

`IntFlag` enumeration controlling the behaviour of `EnvFile` methods.

| Member | Value | Description |
|---|---|---|
| `NONE` | `0` | No flag set |
| `ADD_PLATFORMS_BEFORE` | `1 << 0` | Add platforms to be present in the filenames before the other lists |
| `ADD_PLATFORMS_AFTER` | `1 << 1` | Add platforms to be present in the filenames after the other lists |
| `RESET_ACCUMULATED` | `1 << 2` | Drop internal accumulations from the previous runs |

---

## class `EnvPlatformFlags`

`IntFlag` enumeration controlling `Env.get_cur_platforms(...)` and
`Env.get_all_platforms(...)`.

| Member | Value | Description |
|---|---|---|
| `NONE` | `0` | No flag set |
| `ADD_EMPTY` | `1 << 0` | Add empty string: relevant to any platform |

---

## class `EnvQuoteType`

`IntEnum` enumeration containing information about the kind of quotes removed by
`Env.unquote(...)` or to be set by `Env.quote(...)`.

| Member | Value | Description |
|---|---|---|
| `NONE` | `0` | String with no leading quote |
| `SINGLE` | `1` | Single-quoted string |
| `DOUBLE` | `2` | Double-quoted string |

---

## Dot-env file lookup

The `EnvFile.load()` method looks for the following files. The leading dot is optional; `<sys.platform>` is lowercased; each file is loaded at most once (unless the internal cache is dropped via `EnvFileFlags.RESET_ACCUMULATED`).

**For any filter:**

```
`[.-_]env[.-_]`
```

**Platforms** (added to the list of filters by default):

| Platform | Files (not limited to) |
|---|---|
| Any platform | `.env`, `-env`, `_env`, `env`, `env-`, `env_`, `.env-`, `.env_`, `-env.`, `-env_`, `_env.`, `_env-` |
| Any POSIX platform | `.env.posix`, `[.]posix.env`, `abc.posix-def_env` (has `env` and `posix` parts) |
| Android, Linux | POSIX + `.env.linux`, `[.]linux.env`, `abc.linux-def_env` (has `env` and `linux` parts) |
| BSD-like | POSIX + `.env.bsd`, `[.]bsd.env`, `bsd_abc.def-env.ghi` (has `env` and `bsd` parts) |
| iOS, iPadOS, macOS | BSD + `.env.darwin`, `[.]darwin.env`, and other variations like above |
| VMS | `.env.vms`, `[.]vms.env`, and other variations like above |
| Windows | `.env.windows`, `[.]windows.env`, and other variations like above |
| Java | POSIX or Windows |
| Any platform | `.env.<sys.platform>`, `[.]<sys.platform>.env`, and other variations like above |

If a platform is not listed above explicitly, it still falls into the first
and the last category like the listed ones (e.g. RiscOS or OS/2)

None of these files is required. A file will only be picked if found **and**
verified to be relevant to the platform you are running under. The platform
includes not only OSes but also Java, Cygwin, MSYS and such artefact OSes as
AIX, RiscOS, OpenVMS, OS/2, etc.

In general, 

**Extra filters** can also be passed — things like `"dev"` (runtime environment)
or `"es"` (current language) — as well as a list of all expected runtime
environments and a list of all expected languages. All of that will be considered
while filtering `.env` files in a specified directory. If a filename does not
contain a filterable element, it is treated as common to the whole subset (e.g.
`.env.es` is applicable to any runtime env, or `.env.test` is applicable to any
language when running in `"test"`). The filterable elements can appear in a
filename in any order.

**Example** (`EnvFilter` usage):

```python
EnvFile.get_files(
    EnvFilter(cur_values=['prod'], all_values=['dev', 'test', 'prod', 'production']),
    EnvFilter(cur_values=['jp', 'en'], all_values=['en', 'fr', 'de', 'jp']),
)
```

**Example** (portable Chrome launcher):

```
# .env  (or  .env.any  or  any.env)
APP_NAME = $0
APP_VERSION = "${1}.$2.$3"
APP_FULL_NAME = "$APP_NAME-$APP_VERSION"
PROJECT_PATH = ~/Projects/$APP_FULL_NAME
BROWSER_ARGS = "--opt1 arg1 --opt2 arg2"

# .env.linux  (or  .linux.env  or  linux.env)
CMD_CHROME = "google-chrome $BROWSER_ARGS"

# .env.bsd  (or  .bsd.env  or  bsd.env)
CMD_CHROME = "chrome $BROWSER_ARGS"

# .env.macos  (or  .macos.env  or  macos.env)
CMD_CHROME = "\"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome\" $BROWSER_ARGS"

# .env.windows
CMD_CHROME = "chrome $BROWSER_ARGS"
```

## POSIX-style expansions implemented in _envara_

Windows-style percent-delimited expansions are provided by `Env.expand_posix()` which is called by `Env.expand()`.

### Supported constructs

- Basic variable expansion
  - _$NAME_ and _${NAME}_ - expand variable from the provided _vars_ mapping (defaults to _os.environ_).
  - Positional arguments: _$1_, _$2_, ... (1-based indices supplied via _args_) - out-of-bounds indices leave the pattern unchanged.
  - _$$_ expands to the current process id.

- Length and substrings
  - _${#NAME}_ returns the length of _NAME_'s value.
  - _${NAME:offset[:length]}_ extracts a substring; negative _offset_ counts from the end.

- Defaulting and alternatives
  - _${NAME:-word}_ - use _word_ if _NAME_ is unset or null.
  - _${NAME-word}_ - use _word_ if _NAME_ is unset.
  - _${NAME:+word}_ - use _word_ if _NAME_ is set and non-empty.
  - _${NAME:?message}_ and _${NAME?message}_ - raise _ValueError_ with _message_ if variable is not set (or null for _:?_).

- Assignment
  - _${NAME:=word}_ - set _NAME_ to the expansion of _word_ if _NAME_ is unset or null.
  - _${NAME=word}_ - set _NAME_ if unset.
  - Assignment writes to the _vars_ mapping you pass (if any).

- Pattern removals
  - _${NAME#pattern}_ and _${NAME##pattern}_ - remove shortest/longest matching prefix using glob-style patterns.
  - _${NAME%pattern}_ and _${NAME%%pattern}_ - remove shortest/longest matching suffix using glob-style patterns.

- Substitution
  - _${NAME/pat/repl}_ - replace first match of glob _pat_ with _repl_ (replacement is recursively expanded).
  - _${NAME//pat/repl}_ - replace all matches.
  - Anchored forms: _${NAME/#pat/repl}_ replaces matching prefix, _${NAME/%pat/repl}_ replaces matching suffix.
  - Global anchored forms such as _${NAME//#pat/repl}_ or _${NAME//%pat/repl}_ iteratively apply the anchored substitution until no further progress is made.
  - Empty pattern special cases:
    - _${VAR///X}_ inserts _X_ between every position (including start and end) - tests demonstrate the exact behavior.
    - Anchored empty patterns are treated as no-ops in prefix/suffix anchored forms.

- Escaping
  - A backslash before _$_ or _\`_ prevents expansion: _\\$NAME_ → literal _$NAME_, _\\\`cmd\\\`_ → literal \`cmd\`.
  - Pairs of backslashes reduce appropriately.

- Command substitution
  - _$(...)_ and _\`...\`_ are supported.
  - Inner content is first expanded using _expand_posix()_ before execution (so nested expansions and defaults work inside command substitutions).
  - The executed command's stdout (with trailing newline removed) is inserted into the result.
  - If the command exits with a non-zero status, _ValueError_ is raised (including _stderr_ text in the message).
  - Timeouts raise _ValueError_.

### Safety and configuration

The following parameters control execution of command substitutions and improve safety:

- _expand_flags_: `EnvExpandFlags` (default _EnvExpFlags.DEFAULT_) - controls expansion.
  1. `ALLOW_SHELL` - when set (default), command substitutions are executed with _shell=True_ (less safe, but more flexible).

  2. `ALLOW_SUBPROC` - when set, command substitutions are executed with _shell=False_ using _shlex.split()_ (safer, but requires simple commands and proper quoting).

- _subprocess_timeout_ - timeout in seconds applied to _subprocess.run()_; _TimeoutExpired_ becomes _ValueError_.

Command substitution runs local commands; ensure the expanded input is trusted or use the safety flags to disable or restrict execution. Use these options when expecting to expand untrusted input.

### Development notes

- Unit tests live in _tests/test_trying.py_ and cover:
  - Basic operators and alternatives
  - Pattern removals and substitutions (including anchored and global variants)
  - Nested expansions and defaults
  - Edge cases like empty patterns and replacements equal to original text
  - Command substitution variations and safety flags

- If you add any feature dealing with command execution, add tests that cover both normal and disabled execution modes: `(exp_flags & (EnvExpFlags.ALLOW_SHELL | EnvExpFlags.ALLOW_SUBPROC)) == 0)` as well as timeouts.

## Symmetric (Windows-like) expansions implemented in _envara_

Windows-style percent-delimited expansions are provided by `Env.expand_simple()` which is called by `Env.expand()`. This method supports `%NAME%`, `%1`, `%*`, `%%`, and simple `%~` modifiers (e.g., `%~dp1`) for extracting path components on Windows-like inputs. Additionally, it supports a substring form for named variables using the syntax `%NAME:~start[,length]%` - negative `start` counts from the end. It also supports RiscOS-like variables expansion `<NAME>` as well as OpenVMS-like `'NAME'`.

## Which expansion to choose?

You don't have to decide in the code. It is all about what `EnvFile.load()` encounters first while analysing each line irrespective the platform: dollar or percent. And escape character will be chosen similarly between backslash and caret. However, the POSIX-style assignments are by far more flexible and highly recommended.

## __Good Luck!__