# envara

© Alexander Iurovetski 2026

A library to expand environment variables, application arguments and escape sequences in arbitrary strings, as well as to load stacked env files, remove line comments, unquote and expand values (if the input was unquoted or enclosed in single quotes), execute sub-commands, and finally extend the environment.

Does not depend on any special Python package.

---

## Sample Usage

1. Install _envara_ from _PyPI_

2. In some _.py_ file, try the following:

   ```py
   import os
   from pathlib import Path
   from env import Env
   ...
   # Expand inlline and print the result
   print(Env.expand(r"Home ${HOME:-$USERPROFILE}, arg \#1: $1 # Line comment", plain_args))
   ...
   # Place some .env files into directory below
   EnvFile.load(dir="/home/user/local/bin")

   # Log and check the newly added environment variables
   print(os.environ)
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

---

### `Env.expand()`

> `tuple[str, EnvParseInfo]`

Unquote the input if required via flags, remove trailing line comment if
required via flags, expand the result with the arguments if required via flags,
expand the result with the environment variables' values. The method follows
POSIX and DOS/Windows expansion conventions depending on what was found first:
dollar or percent, then backslash or caret (obviously, the POSIX style is by far
more advanced).

```python
@staticmethod
def expand(
    input: str,
    args: list[str] | None = None,
    flags: EnvExpandFlags | None = None,
    strip_spaces: bool = True,
    escape_chars: str = None,
    expand_chars: str = None,
    hard_quotes: str = None,
    cutter_chars: str = None,
) -> tuple[str, EnvParseInfo]: ...
```

**Parameters**

| Name | Type | Description |
|---|---|---|
| `input` | `str` | String to expand |
| `args` | `list[str] \| None` | List of arguments to expand `$#`, `$1`, `$2`, … |
| `flags` | `EnvExpandFlags \| None` | Flags controlling what/how to expand input |
| `strip_spaces` | `bool` | `True` if can remove spaces from the start and end of `input` |
| `escape_chars` | `str` | String of chars to treat as escape chars |

**Returns** — Expanded string.

---

### `Env.expand_posix()`

> `str`

Expand environment variables and sub-processes according to complex POSIX rules:
like `${ABC:-${DEF:-$(uname -a)}}`. See the description of arguments under the
main method `expand(...)`.

```python
@staticmethod
def expand_posix(
    input: str,
    args: list[str] | None = None,
    vars: dict[str, str] | None = os.environ,
    expand_char: str = EnvParseInfo.POSIX_EXPAND_CHAR,
    escape_char: str = EnvParseInfo.POSIX_ESCAPE_CHAR,
    expand_flags: EnvExpandFlags = EnvExpandFlags.DEFAULT,
    subprocess_timeout: float | None = None,
) -> str: ...
```

**Returns** — Expanded string.

---

### `Env.expand_simple()`

> `str`

Expand environment variables and sub-processes according to simple rules and
symmetric expand characters: like `%ABC%` in Windows. See the description of
arguments under the main method `expand(...)`.

```python
@staticmethod
def expand_simple(
    input: str,
    args: list[str] | None = None,
    vars: dict[str, str] | None = None,
    expand_char: str = EnvParseInfo.WINDOWS_EXPAND_CHAR,
    escape_char: str = EnvParseInfo.WINDOWS_ESCAPE_CHAR,
) -> str: ...
```

**Returns** — Expanded string.

---

### `Env.get_all_platforms()`

> `list[str]`

Get the list of all supported platforms (see `Env.__platform_map`).

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

Reads series of `key=value` lines from dot-env files, removes line comments,
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

Get list of eligible dot-env files. Adds a list of platform names if
`flags` includes `EnvFileFlags.ADD_PLATFORMS` (default).

```python
@staticmethod
def get_files(
    dir: Path | None = None,
    indicator: str | None = None,
    flags: EnvFileFlags = EnvFileFlags.ADD_PLATFORMS,
    *filters: list[EnvFilter] | EnvFilter,
) -> list[Path]: ...
```

**Parameters**

| Name | Type | Description |
|---|---|---|
| `dir` | `Path \| None` | Directory to look in |
| `indicator` | `str \| None` | Necessary part of every relevant filename |
| `flags` | `EnvFileFlags` | Add platform names to filters (default: `EnvFileFlags.ADD_PLATFORMS`) |
| `*filters` | `EnvFilter` | One or more `EnvFilter` objects specifying current values and possibilities |

**Returns** — List of matching paths in the given directory.

---

### `EnvFile.load()`

Add key-expanded-value pairs from `.env`-compliant file(s) to `os.environ`.

```python
@staticmethod
def load(
    dir: Path | None = None,
    file_flags: EnvFileFlags = EnvFileFlags.ADD_PLATFORMS,
    args: list[str] | None = None,
    expand_flags: EnvExpandFlags = DEFAULT_EXPAND_FLAGS,
    *filters: list[str] | str | None,
): ...
```

**Parameters**

| Name | Type | Description |
|---|---|---|
| `dir` | `Path \| str \| None` | Default directory to locate platform-specific files |
| `file_flags` | `EnvFileFlags` | Describes what and how to load |
| `args` | `list[str] \| None` | List of arguments (e.g. application args) to expand placeholders like `$1`, `${2}`, … |
| `expand_flags` | `EnvExpandFlags` | Describes how to expand env vars and app args |

---

### `EnvFile.load_from_str()`

Add key-expanded-value pairs from a string buffer to `os.environ`.

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
    flags: EnvFileFlags = EnvFileFlags.ADD_PLATFORMS,
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
| `DEFAULT_INDICATOR` | `str` | Default dot-env file type without leading extension separator (`"env"`) |
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

**Parameters**

| Name | Type | Description |
|---|---|---|
| `indicator` | `str \| None` | A necessary part of a name (always present), default: `DEFAULT_INDICATOR` |
| `cur_values` | `list[str] \| str \| None` | One or more strings relevant to the current run, passed either as a list or a single string |
| `all_values` | `list[str]` | All possible values passed as a list of strings |

---

### `EnvFilter.is_match()`

> `bool`

Check the input matches the given filters:

- Should match the default (indicator) pattern.
- Should either match the current values or not match the whole set at all.
  For example, `.en.prod` matches `.env.en`, `fr.env` and `_jp_env`,
  but neither `.prod.es` nor `.es_prod` match.

```python
def is_match(
    self,
    input: list[str] | str | None,
) -> bool: ...
```

**Returns** — `True` if the input matches, `False` otherwise.

---

### `EnvFilter.to_regex()`

> `re.Pattern`

Convert a glob or regex pattern string into a compiled `re.Pattern`.

```python
@staticmethod
def to_regex(
    indicator: str = DEFAULT_INDICATOR,
    input: list[str] | str | None = None,
    is_full: bool = True,
) -> re.Pattern: ...
```

**Parameters**

| Name | Type | Description |
|---|---|---|
| `indicator` | `str \| None` | Required part of a name (always present), default: `DEFAULT_INDICATOR` |
| `input` | `list[str] \| str \| None` | Comma-separated string or a list of strings with optional wildcards: `"linux,*os"` or `["en", "es", "fr"]` or `"dev,*test*,prod*"` |
| `is_full` | `bool` | `True` = wrap into `^...$` |

**Returns** — Regular expression matching the passed criteria.

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
| `PWSH_CUTTER_CHAR` | `str` | `"#"` | PowerShell line comment character |
| `PWSH_EXPAND_CHAR` | `str` | `"$"` | PowerShell variable expansion character |
| `PWSH_ESCAPE_CHAR` | `str` | `` "`" `` | PowerShell escape character |
| `WINDOWS_CUTTER_CHAR` | `str` | `";"` | Windows/DOS line comment character |
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
    escape_char: str | None = None,
    cutter_char: str | None = None,
    quote_type: EnvQuoteType = EnvQuoteType.NONE,
): ...
```

**Parameters**

| Name | Type | Description |
|---|---|---|
| `input` | `str` | String being unquoted |
| `result` | `str` | Result of unquoting |
| `expand_char` | `str` | First non-escaped and non-quoted expand character encountered: dollar, percent, angle bracket |
| `escape_char` | `str` | First non-escaped and non-quoted escape character encountered: backslash, backtick, caret |
| `cutter_char` | `str` | First non-escaped and non-quoted character recognised as the end of data in a string (like a line comment start): hash |
| `quote_type` | `EnvQuoteType` | Type of enclosing quotes found |

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
| `ADD_PLATFORMS` | `1 << 0` | Add platforms to be present in the filenames |
| `RESET_ACCUMULATED` | `1 << 1` | Drop internal accumulations from the previous runs |

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

The `EnvFile.load()` method looks for the following files. The leading dot is
optional, except for `.env`; `<sys.platform>` is lowercased; each file is loaded
at most once (unless the internal cache is dropped via
`EnvFileFlags.RESET_ACCUMULATED`).

**For any filter:**

```
.env
```

**Platforms** (added to the list of filters by default):

| Platform | Files |
|---|---|
| Android, Linux | `.env.posix`, `[.]posix.env`, `.env.linux`, `[.]linux.env` |
| BSD-like | `.env.posix`, `[.]posix.env`, `.env.bsd`, `[.]bsd.env` |
| Cygwin, MSYS | `.env.posix`, `[.]posix.env` |
| iOS, iPadOS, macOS | `.env.posix`, `[.]posix.env`, `.env.bsd`, `[.]bsd.env`, `.env.darwin`, `[.]darwin.env` |
| Java | `.env.posix`, `[.]posix.env` (POSIX) or `.env.windows`, `[.]windows.env` (Windows) |
| VMS | `.env.vms`, `[.]vms.env` |
| Windows | `.env.windows`, `[.]windows.env` |
| Any platform | `.env.<sys.platform>`, `[.]<sys.platform>.env` |

None of these files is required. A file will only be picked if found **and**
verified to be relevant to the platform you are running under. The platform
includes not only OSes but also Java, Cygwin, MSYS and such artefact OSes as
AIX, RiscOS, OpenVMS, OS/2, etc.

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
    EnvFilter(cur_values='prod*', all_values=['dev', 'test', 'prod', 'production']),
    EnvFilter(cur_values=['jp', 'en'], all_values='en,fr,de,jp'),
)
```

**Example** (portable Chrome launcher):

```
# .env  (or  .env.any  or  any.env)
APP_NAME = $1
APP_VERSION = "${2}_$3"
PROJECT_PATH = ~/Projects/$APP_NAME
ARG_HEADLESS = "--headless --disable-gpu --default-background-color=00000000 --window-size={w},{h} --screenshot={o} file://{i}"

# .env.linux  (or  .linux.env  or  linux.env)
CMD_CHROME = "google-chrome $ARG_HEADLESS"

# .env.bsd  (or  .bsd.env  or  bsd.env)
CMD_CHROME = "chrome $ARG_HEADLESS"

# .env.macos  (or  .macos.env  or  macos.env)
CMD_CHROME = "\"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome\" $ARG_HEADLESS"

# .env.windows
CMD_CHROME = "chrome $ARG_HEADLESS"
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
  - A backslash before _$_ or backtick prevents expansion: _\$NAME_ → literal _$NAME_, __\_cmd\_ __ → literal __ _cmd_ __.
  - Pairs of backslashes reduce appropriately.

- Command substitution
  - _$(...)_ and __ _..._ __ are supported.
  - Inner content is first expanded using _expand_posix()_ before execution (so nested expansions and defaults work inside command substitutions).
  - The executed command's stdout (with trailing newline removed) is inserted into the result.
  - If the command exits with a non-zero status, _ValueError_ is raised (including _stderr_ text in the message).
  - Timeouts raise _ValueError_.

### Safety and configuration

The following parameters control execution of command substitutions and improve safety:

- _expand_flags: EnvExpFlags_ (default _EnvExpFlags.DEFAULT_) - controls expansion.
  1. _ALLOW_SHELL_ - when set (default), command substitutions are executed with _shell=True_ (less safe, but more flexible).

  2. _ALLOW_SUBPROC_ - when set, command substitutions are executed with _shell=False_ using _shlex.split()_ (safer, but requires simple commands and proper quoting).

- _subprocess_timeout_ - timeout in seconds applied to _subprocess.run()_; _TimeoutExpired_ becomes _ValueError_.

Command substitution runs local commands; ensure the expanded input is trusted or use the safety flags to disable or restrict execution. Use these options when expecting to expand untrusted input.

### Development notes

- Unit tests live in _tests/test_trying.py_ and cover:
  - Basic operators and alternatives
  - Pattern removals and substitutions (including anchored and global variants)
  - Nested expansions and defaults
  - Edge cases like empty patterns and replacements equal to original text
  - Command substitution variations and safety flags

- If you add any feature dealing with command execution, add tests that cover both normal and disabled execution modes: _(exp\_flags & (EnvExpFlags.ALLOW\_SHELL | EnvExpFlags.ALLOW\_SUBPROC)) == 0)_ as well as timeouts.

## Symmetric (Windows-like) expansions implemented in _envara_

Windows-style percent-delimited expansions are provided by `Env.expand_symmetric()` which is called by `Env.expand()`. This method supports _%NAME%_, _%1_, _%*_, _%%_, and simple _%~_ modifiers (e.g., _%~dp1_) for extracting path components on Windows-like inputs. Additionally, it supports a substring form for named variables using the syntax _%NAME:~start[,length]%_ - negative _start_ counts from the end. The older name _expand_windows_ was removed and replaced by _expand_symmetric_ to better reflect its general-purpose nature.

## Which expansion to choose?

You don't have to decide in the code. It is all about what `EnvFile.load()` encounters first while analysing each line irrespective the platform: dollar or percent. And escape character will be chosen similarly between backslash and caret. However, the POSIX-style assignemnts are by far more flexible and highly recommended.

## __Good Luck!__