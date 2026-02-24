# envara (C) Alexander Iurovetski 2026

## A library to remove line comments, expand environment variables, application arguments and special characters in a string, execute sub-commands, as well as parse general and OS-specific .env files

This library does not depend on any special Python package.

### Sample Usage

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

### How to Expand Environment Variables and Arguments in a String

__*Env.expand*__ _(input: str, args: list\[str\] = None, flags: EnvExpandFlags = EnvExpandFlags.DEFAULT, ) -> str_

(see also _POSIX-style expansions implemented in envara_ at the bottom of this page)

1. _input_: a string to expand

   Some string that might contain references to environment variables, user home and/or your application's command-line arguments: _Home ~, Abc: $ABC, arg #1: $1_. For any non-existent environment variable or an index outside the boundaries, the pattern will remain untouched.

2. _args_: a list of command-line arguments (optional)

   These could be plain arguments left after parsing command-line options.

3. _flags_: a bitwise combination of flags listed under the _EnvExpandFlags_ enumeration:

   - _NONE_: none of the below (default)
   - _REMOVE\_LINE\_COMMENT_: remove hash _#_ (outside the quotes if found) and everything beyond that
   - _REMOVE\_QUOTES_: remove leading and trailing quotes
   - _SKIP\_ENVIRON_: do not expand environment variables
   - _SKIP\_SINGLE\_QUOTED_: if a string is enclosed in apostrophes, don't expand it (default in _EnvFile.read\_text()_).
   - _UNESCAPE_: expand escaped characters: _\\\\_, _\\n_, _\\uNNNN_, etc.

4. _default\_dir_: directory to locate the default files

   If not specified, the directory of the first parameter will be used (a parent of a file if file, or itself if directory). If the first parameter is not specified either, the current directory will be used.

5. _Return value_

   A copy of the first parameter expanded as described above.

__*Env.expandargs*__ _(input: str, args: list\[str\] = None) -> str_

1. _input_: a string to expand

   Some string that might contain 1-based references to your application's command-line arguments or any other list of strings: _Project Name: $1_. For any index outside the boundaries, the pattern will remain untouched.

2. _args_ - a list of command-line arguments (optional, although a bit pointless)

   These could be plain arguments left after parsing command-line options.

3. _Return value_

   A copy of the first parameter expanded as described above.

__*Env.get_cur_platforms*__ _(flags: EnvPlatformFlags = EnvPlatformFlags.DEFAULT, prefix: str = None, suffix: str = None) -> list\[str\]_

1. Param _flags_

   A bitwise combination of:

   - _NONE_: none of the below
   - _ADD\_EMPTY_: relevant to any platform
   - _ADD\_CURRENT_: add current platform, relevant to any platform
   - _ADD\_MAX_: add maximum platforms

2. Param _prefix_

   An optional free text to put in front of every platform name in the resulting list; in a call from _EnvFile.read\_text()_, is set to a dot when needed.

3. Param _suffix_

   An optional free text to put after every platform name in the resulting list; in a call from _EnvFile.read\_text()_, is set to _.env_ always.

4. Return value

   A copy of the first parameter quoted as per the second argument.

__*Env.quote*__ _(input: str, type: EnvQuoteType = EnvQuoteType.DOUBLE) -> str_

1. Param _input_

   A string to enclose in quotes. Might contain an escape character _\\_ and/or internal similar quotes, all of those will be escaped with another _\\_.

2. Param _type_

   Type of the quote as one of the following _EnvQuoteType_ values: _NONE_, _SINGLE_ or _DOUBLE_.

3. Return value

   A copy of the first parameter quoted as per the second argument.

__*Env.remove_line_comment*__ _(input: str) -> str_

1. Param _input_

   A string to clean. For multiline strings, it is highly recommended to split those into a list, then to call this method on each item. You'll process the input line-by-line anyway.

2. Return value

   A copy of the first parameter with everything beyond the first encountered outside string literals hash symbol _#_.

__*Env.unquote*__ _(input: str, unescape: bool = True) -> tuple[str, EnvQuoteType]_

1. Param _input_

   A string to remove enclosing quotes from. Might contain escaped characters like _\\t_, _\\n_, _\\uNNNN_, etc., as well as escaped similar quote. All of those will be converted to the respected unescaped characters in case of a double-quoted _input_, and _unescape_ set. A single-quoted one will remain intact: just the enclosing quotes removed. If the string doesn't start with the expected quote, only decoding of escaped characters might be performed. If no closing quote found, a _ValueError_ will be raised.

2. Param _unescape_

   If True, and _input_ is not single-quoted, then unescape escaped characters (see Param _input_ for more detail).

3. Return value

   A tuple of the first parameter unquoted, and the type of quotes encountered. This can be used to determine which quotes the string had were before.

## POSIX-style expansions implemented in envara

This document describes the behaviour implemented in _Env.expand_posix()_ and the testing and safety guidance for using these features.

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

### Sample Usage of Env.expand...()

___py
from env import Env

\# Expand a string with environment variables and defaults

res = Env.expand_posix("Home: ${HOME:-/home/default}, first arg: $1", args=["app"], expand_flags=EnvExpFlags.ALLOW_SHELL)

\# Run a simple command substitution without shell

res2 = Env.expand_posix('$(printf "%s" $FOO)', expand_flags=EnvExpFlags.ALLOW_SUBPROCESS)
___

## Symmetric (Windows-like) expansions implemented in envara

Windows-style percent-delimited expansions are provided by _Env.expand_symmetric()_ (see _envara.env_). This method supports _%NAME%_, _%1_, _%*_, _%%_, and simple _%~_ modifiers (e.g., _%~dp1_) for extracting path components on Windows-like inputs. Additionally, it supports a substring form for named variables using the syntax _%NAME:~start[,length]%_ - negative _start_ counts from the end. The older name _expand_windows_ was removed and replaced by _expand_symmetric_ to better reflect its general-purpose nature.

## Which expansion to choose?

You don't have to decide in the code. It is all about what _EnvFile.load()_ encounters while analysing the content. Whatever comes first in each line ($ or %), will be used, and escape character will be chosen similarly. However, the POSIX-style assignemnts are by far more flexible. On the other hand, _EnvFile.load()_ handles both styles on any platform.

## __Good Luck!__
