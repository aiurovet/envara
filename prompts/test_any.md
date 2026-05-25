Create tests as follows:

- use pytest
- should be recognized by pytest-cov
- mock all classes except the one being tested
- parametrize as much as possible
- ensure maximum coverage (at least 80%)
- ensure tests will produce the same results when run on different platforms by:
  - mocking os.sep
  - mocking EnvChars.IS_POSIX, EnvChars.IS_RISCOS, EnvChars.IS_VMS and EnvChars.IS_WINDOWS
  - mocking Env.IS_POSIX, Env.IS_RISCOS, Env.IS_VMS and Env.IS_WINDOWS
  - passing Env.POSIX, Env.RISCOS, Env.VMS and Env.WINDOWS as parameter chars where applicable
