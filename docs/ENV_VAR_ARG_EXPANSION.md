# POSIX-style expansions implemented in envara

This document describes the behaviour implemented in `Trying.expand_posix()` and the testing and safety guidance for using these features.

## Supported constructs

- Basic variable expansion
  - `$NAME` and `${NAME}` — expand variable from the provided `vars` mapping (defaults to `os.environ`).
  - Positional arguments: `$1`, `$2`, ... (1-based indices supplied via `args`) — out-of-bounds indices leave the pattern unchanged.
  - `$$` expands to the current process id.

- Length and substrings
  - `${#NAME}` returns the length of `NAME`'s value.
  - `${NAME:offset[:length]}` extracts a substring; negative `offset` counts from the end.

- Defaulting and alternatives
  - `${NAME:-word}` — use `word` if `NAME` is unset or null.
  - `${NAME-word}` — use `word` if `NAME` is unset.
  - `${NAME:+word}` — use `word` if `NAME` is set and non-empty.
  - `${NAME:?message}` and `${NAME?message}` — raise `ValueError` with `message` if variable is not set (or null for `:?`).

- Assignment
  - `${NAME:=word}` — set `NAME` to the expansion of `word` if `NAME` is unset or null.
  - `${NAME=word}` — set `NAME` if unset.
  - Assignment writes to the `vars` mapping you pass (if any).

- Pattern removals
  - `${NAME#pattern}` and `${NAME##pattern}` — remove shortest/longest matching prefix using glob-style patterns.
  - `${NAME%pattern}` and `${NAME%%pattern}` — remove shortest/longest matching suffix using glob-style patterns.

- Substitution
  - `${NAME/pat/repl}` — replace first match of glob `pat` with `repl` (replacement is recursively expanded).
  - `${NAME//pat/repl}` — replace all matches.
  - Anchored forms: `${NAME/#pat/repl}` replaces matching prefix, `${NAME/%pat/repl}` replaces matching suffix.
  - Global anchored forms such as `${NAME//#pat/repl}` or `${NAME//%pat/repl}` iteratively apply the anchored substitution until no further progress is made.
  - Empty pattern special cases:
    - `${VAR///X}` inserts `X` between every position (including start and end) — tests demonstrate the exact behavior.
    - Anchored empty patterns are treated as no-ops in prefix/suffix anchored forms.

- Escaping
  - A backslash before `$` or backtick prevents expansion: `\$NAME` → literal `$NAME`, ``\`cmd\` `` → literal `` `cmd` ``.
  - Pairs of backslashes reduce appropriately.

- Command substitution
  - `$(...)` and `` `...` `` are supported.
  - Inner content is first expanded using `expand_posix()` before execution (so nested expansions and defaults work inside command substitutions).
  - The executed command's stdout (with trailing newline removed) is inserted into the result.
  - If the command exits with a non-zero status, `ValueError` is raised (including `stderr` text in the message).
  - Timeouts raise `ValueError`.

## Safety and configuration

The following parameters control execution of command substitutions and improve safety:

- `allow_subprocess: bool` (default `True`) — when `False`, command substitutions are left intact and not executed.
- `allow_shell: bool` (default `True`) — when `False`, commands are executed with `shell=False` using `shlex.split()` (safer, but requires simple commands and proper quoting).
- `subprocess_timeout` — timeout in seconds applied to `subprocess.run()`; `TimeoutExpired` becomes `ValueError`.

Use these options when expanding untrusted input.

## Development notes

- Unit tests live in `tests/test_trying.py` and cover:
  - Basic operators and alternatives
  - Pattern removals and substitutions (including anchored and global variants)
  - Nested expansions and defaults
  - Edge cases like empty patterns and replacements equal to original text
  - Command substitution variations and safety flags

- If you add any feature dealing with command execution, add tests that cover both normal and disabled execution modes (`allow_subprocess=False`) and timeouts.

## Example usage

```py
from envara.trying import Trying

# Expand a string with environment variables and defaults
res = Trying.expand_posix("Home: ${HOME:-/home/default}, first arg: $1", args=["app"], allow_subprocess=False)

# Run a simple command substitution without shell
res2 = Trying.expand_posix('$(printf "%s" $FOO)', allow_subprocess=True, allow_shell=False)
```

## Windows / symmetric expansion note

Windows-style percent-delimited expansions are provided by `Trying.expand_symmetric()` (see `envara.trying`). This method supports `%NAME%`, `%1`, `%*`, `%%`, and simple `%~` modifiers (e.g., `%~dp1`) for extracting path components on Windows-like inputs. Additionally, it supports a substring form for named variables using the syntax `%NAME:~start[,length]%` — negative `start` counts from the end. The older name `expand_windows` was removed and replaced by `expand_symmetric` to better reflect its general-purpose nature.

## Security reminder

Command substitution runs local commands; ensure the expanded input is trusted or use the safety flags to disable or restrict execution.
