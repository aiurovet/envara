# envara (C) Alexander Iurovetski 2026

## A library to expand environment variables, program arguments and special characters in a string, as well as parse general and OS-specific .env  files

This library allows to expand environment variables and program arguments in a string, parse general and OS-specific .env  files.

The application does not depend on any special Python package.

### Usage

This example can be used to generate all launcher icons for a _Flutter_ project. See also: _How Do I Use It_ at the end of this document

1. Install _envara_ from _PyPI_

2. In some _.py_ file, try the following:

   ```py
   from pathlib import Path
   from envara import Env
   ...
   Env.expand("Home $HOME, arg #1: $1", plain_args)
   ...
   DotEnv.load_from_file(Path("/path/to/.my.env"), default_dir="/home/user/local/bin")
   ```

### How to Expand Environment Variables and Arguments in a String

__*Env.expand*__ _(input: str, args: list\[str\] = None, flags: EnvExpandFlags = EnvExpandFlags.DEFAULT) -> str_

1. _input_: a string to expand

   Some string that might contain references to environment variables, user home and/or your application's command-line arguments: _Home ~, Abc: $ABC, arg #1: $1_. For any non-existent environment variable or an index outside the boundaries, the pattern will remain untouched.

2. _args_: a list of command-line arguments (optional)

   These could be plain arguments left after parsing command-line options.

3. _flags_: a bitwise combination of flags listed under the _EnvExpandFlags_ enumeration:

   - _NONE_: none of the below (default)
   - _REMOVE\_LINE\_COMMENT_: remove hash _#_ (outside the quotes if found) and everything beyond that
   - _REMOVE\_QUOTES_: remove leading and trailing quotes
   - _SKIP\_ENVIRON_: do not expand environment variables
   - _SKIP\_SINGLE\_QUOTED_: if a string is enclosed in apostrophes, don't expand it (default in _DotEnv.read\_text()_).
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

__*Env.get_platform_stack*__ _(flags: EnvPlatformStackFlags = EnvPlatformStackFlags.DEFAULT, prefix: str = None, suffix: str = None) -> list\[str\]_

1. Param _flags_

   A bitwise combination of:

   - _NONE_: none of the below
   - _ADD\_EMPTY_: relevant to any platform
   - _ADD\_CURRENT_: add current platform, relevant to any platform
   - _ADD\_MAX_: add maximum platforms

2. Param _prefix_

   An optional free text to put in front of every platform name in the resulting list; in a call from _DotEnv.read\_text()_, is set to a dot when needed.

3. Param _suffix_

   An optional free text to put after every platform name in the resulting list; in a call from _DotEnv.read\_text()_, is set to _.env_ always.

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

### How to Load .env file

__*DotEnv.load\_from\_file*__ _(path: Path, file\_flags: DotEnvFileFlags = DotEnvFileFlags.DEFAULT, expand\_flags: EnvExpandFlags = EnvExpandFlags.DEFAULT, default\_dir: str = None, alt\_ext: str = None) -> str_

A mere wrapper calling _DotEnv.read\_text()_, then  _DotEnv.load\_from\_str()_. See more detail there.

__*DotEnv.load\_from\_str*__ _(data: Path, expand\_flags: EnvExpandFlags = EnvExpandFlags.DEFAULT) -> str_

1. Param _data_

   The input to expand. _DotEnv.load\_from\_file()_ loads content from file(s), then passes that buffer as this parameter.

2. Param _expand\_flags_

   A bitwise combination. See _flags_ under _Env.expand()_ for more detail.

__*DotEnv.read\_text*__ _(path: Path, file\_flags: DotEnvFileFlags = DotEnvFileFlags.DEFAULT, default\_dir: str = None, alt\_ext: str = None) -> str_

1. Param _path_

   A file or directory. If file, will be loaded after the default ones (see below). If directory, will be used to locate the default files in, if _None_, the current directory will be used.

2. Param _file\_flags_

   A bitwise combination of:

   - _NONE_: none of the below (default)
   - _RESET_: discard internally accumulated list of loaded files
   - _SKIP\_DEFAULT\_FILES_: do not load any default file
   - _VISIBLE\_FILES_: do not prepend default filenames with a dot, except _.env_

3. Param _default\_dir_

   Directory to look for the default files in. If not specified, the directory of the first parameter _path_ will be used if passed, or the current directory otherwise.

4. Param _alt\_ext_

   Alternative extension to use

### The Default .env Files

These files will be loaded in the noted order before the custom one. This happens in _DotEnv.read\_text()_, which is called by _DotEnv.load\_from\_file()_.

Note that _sys.platform_ is converted to lowercase, all comparisons are case-insensitive, file extension can be changed.

- _.env_ (always hidden), then _[.]any.env_

  For any _sys.platform_.

- _[.]posix.env_

  When _sys.platform_ contains one of the following: _aix_, _bsd_, _darwin_, _hp-ux_, _linux_, _sunos_, _java_ (on POSIX OS), _cygwin_, _MSYS_.

- _[.]bsd.env_

  When _sys.platform_ contains _bsd_ or _darwin_.

- _[.]linux.env_

  When _sys.platform_ contains _linux_.

- _[.]darwin.env_

  When _sys.platform_ contains _darwin_ or _macos_, or starts with _ios_ (the latter also applies to iPadOS).

- _[.]macos.env_

  When _sys.platform_ contains _darwin_ or _macos_.

- _[.]vms.env_

  When _sys.platform_ contains _vms_.

- _[.]windows.env_

  When _sys.platform_ starts with _win_ or contains _java_ that is running on Windows.

- _[.]\<sys.platform\>.env_

  For any _sys.platform_ again.

### How to Utilise the Stack of Default _.env_ Files

For instance, you are going to call _Google Chrome_ from your script in headless mode to save some screenshots. In that case, you can define variables _ARG\_HEADLESS_ and _CMD\_CHROME_ as follows:

- _.env_:

    APP_NAME = $1 \# need to pass a list of command-line arguments

    APP_VERSION = "${2}_$3"

    PROJECT_PATH = ~/Projects/$APP_NAME

    ARG_HEADLESS = "--headless --disable-gpu --default-background-color=00000000 --window-size={w},{h} --screenshot={o} file://{i}"

- _.linux.env_:

    CMD_CHROME = "google-chrome $ARG_HEADLESS"

- _.bsd.env_:

    CMD_CHROME = "chrome $ARG_HEADLESS"

- _.macos.env_:

    CMD_CHROME = "\\"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome\\" $ARG_HEADLESS"

- _.windows.env_:

    CMD_CHROME = "chrome $ARG_HEADLESS"

## __Good Luck!__
