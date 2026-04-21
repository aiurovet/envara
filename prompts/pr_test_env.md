<!--
Remove tests/test_env.py (if exists) and execute prompts/pr_test_env.md
-->

Execute prompts/pr_test_any.md ensuring that:

## unquote
- Called during expand
- Contains parametrized test called test_unquote that:
  - has the following parameters: input_str, flags, chars, expected
  - ensures maximum coverage
- Checks returned quote_type depending on the surrounding quotes

## method expand:
- Mocks other methods of Env
- Sets flags to default when passed as None
- Calls unquote when needed
- Calls expand_posix or expand_simple with empty dict for vars when EnvExpandFlags.SKIP_ENV_VARS is set
- Returns Path if input is Path, otherwise returns str
- Skips expansion (no expand_posix or expand_simple called) when string is hard-quoted (EnvQuoteType.HARD with EnvExpandFlags.SKIP_HARD_QUOTED)
- Routes to expand_posix when expand_char is "$" (POSIX)
- Routes to expand_simple when expand_char is "%" (Windows), "<" (RISCOS), or "'" (VMS)
- Calls unescape when needed

## methods expand_posix and expand_simple:
- Contains parametrized tests called test_expand_posix and test_expand_simple that:
  - has the following parameters: input_str, vars, args, expected
  - assigns vars to mocked os.environ
  - when vars is None, but os.environ has some values, those will be used in place of vars
  - ensures maximum coverage within the rules for POSIX and Windows expansions
- Returns Path if input is Path, otherwise returns str

## method unescape
- Contains parametrized test called test_unquote that:
  - has the following parameters: input_str, strip_blanks, chars, expected
  - ensures maximum coverage
  - tests for all platforms