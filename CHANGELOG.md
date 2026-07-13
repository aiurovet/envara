## 0.6.2

Added `Env.break_args()` to make 2 lists: the one with "proper" arguments, and the one with things like pipes or I/O re-direction, and beyond
Added `Env.join()` to join arguments into a single command, the opposite to `Env.split()`

## 0.6.1

Had to bump the version due to stopped upload

## 0.6.0

Removed support for RiscOS, as it was removed from Python 3+, fixed detection of VMS, adjusted tests, introduced `EnvCharsData.cmd_ops`, `EnvCharsData.split_glued()` and made `Env.split()` more advanced (breaking where needed, but no space character found). Fixed `Env.unquote()`: if _flags_ has UNQUOTE not set, should not unquote.

## 0.5.7

Scripts `py_upload.*` can figure out project name

## 0.5.6

Added `EnvFile.DEFAULT_SUFFIX` (default file type, or the filename extension)

## 0.5.5

Bugfix: every variable in each env file should be expanded according to the rules defined by the first line starting with a cutter char

## 0.5.4

Updated README.md, improved example and tests

## 0.5.3

Adding EnvChars.POSIX_WINDOWS to make POSIX-style expansions available on Windows

## 0.5.2

Bugfix: in `Env.expand()`, convert `os.sep` to `os.altsep` or the other way round if one of those coincides with `chars.escape` (mainly, for POSIX-style conversions on Windows)

## 0.5.1

Improved `Env.expand_path()` and added  `Env.strip()`

## 0.5.0

Added expansion of a user-specific directory in `Env.expand_path()`, made expansion rules for the command-line arguments similar to the ones for the environment variables, fixed Pylance issues in test_env.py

## 0.4.2

Removed unnecessary type specifiers, fixed a few failing and xpassed tests

## 0.4.1

Documentation corrected

## 0.4.0

Added static method `split_command()` to `Env` that allows to split command into array of an executable and its arguments (OS-agnostic)

Breaking changes: mainly, a switch from multiple parameters (for various platform-specific characters) to a single object of the class `EnvCharsData`. It also decides on which platform's rules to use for the variables' expansions in env files based on the first non-empty character(s) representing a start of a line comment. Previously, it was searching for specific patterns in every line. Finally, public methods `Env.expand_posix(...)` and `Env.expand_simple(...)` have been moved to the private scope, so stop using those directly in favour of `Env.expand(...)`.

## 0.3.0

Added static methods `get_default_*_char()` to `EnvParseInfo` and initialized omitted arguments in `Env.quote()` and `Env.unescape()` using those

## 0.2.0

`Env.expand()`, `Env.expand_posix()` and `Env.expand_simple()` will return `Path` if `input` is `Path` rather than `str`

## 0.1.0

Improved documentation, a bugfix for the default value for parameters of the type `EnvExpandFlags`, a bugfix for stripping blanks

## 0.0.9

Switched to the string search instead of complex regexes when looking for a given value in a string, added windup_char(s) to perform Env.expand_simple(...) on a pair of different opening and closing characters like `<VAR>` for RiscOS, improved documentation

## 0.0.8

- Added the out_info parameter to Env.expand() as well as a method EnvParseInfo.copy_to()

## 0.0.7

- Documentation improved

## 0.0.6

- Documentation extended, swapped the order of a couple of arguments in a method

## 0.0.5

- Changed `Env.expand()` to return just an expanded string rather than a tuple, added fully functioning example under `examples/`, fixed a bug for an empty EnvFilter check, fixed example in README.md

## 0.0.4

- A fix for importing the package.

## 0.0.3

- Initial release to PyPI.

## 0.0.2

- Fixed `__main__.py` by moving the most of the code under _def main()_

## 0.0.1

- Initial release to TestPyPI.
