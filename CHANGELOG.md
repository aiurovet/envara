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
