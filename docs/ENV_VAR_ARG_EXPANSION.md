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

- _exp_flags: EnvExpFlags_ (default _EnvExpFlags.DEFAULT_) - controls expansion.
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

- If you add any feature dealing with command execution, add tests that cover both normal and disabled execution modes (_(exp_flags & (EnvExpFlags.ALLOW_SHELL | EnvExpFlags.ALLOW_SUBPROC)) == 0_) as well as timeouts.

### Sample Usage

___py
from env import Env

\# Expand a string with environment variables and defaults

res = Env.expand_posix("Home: ${HOME:-/home/default}, first arg: $1", args=["app"], exp_flags=EnvExpFlags.ALLOW_SHELL)

\# Run a simple command substitution without shell

res2 = Env.expand_posix('$(printf "%s" $FOO)', exp_flags=EnvExpFlags.ALLOW_SUBPROCESS)
___

## Symmetric (Windows-like) expansions implemented in envara

Windows-style percent-delimited expansions are provided by _Env.expand_symmetric()_ (see _envara.env_). This method supports _%NAME%_, _%1_, _%*_, _%%_, and simple _%~_ modifiers (e.g., _%~dp1_) for extracting path components on Windows-like inputs. Additionally, it supports a substring form for named variables using the syntax _%NAME:~start[,length]%_ - negative _start_ counts from the end. The older name _expand_windows_ was removed and replaced by _expand_symmetric_ to better reflect its general-purpose nature.

## Which expansion to choose?

You don't have to decide in the code. It is all about what _EnvFile.load()_ encounters while analysing the content. Whatever comes first in each line ($ or %), will be used, and escape character will be chosen similarly. However, the POSIX-style assignemnts are by far more flexible. On the other hand, _EnvFile.load()_ handles both styles on any platform.
