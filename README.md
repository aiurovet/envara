# envara (C) Alexander Iurovetski 2026

## A library to expand environment variables, program arguments and special characters in a string, as well as parse general and OS-specific .env  files

This library allows to expand environment variables and program arguments in a string, parse general and OS-specific .env  files.

The application does not depend on any special Python package.

### Usage

This example can be used to generate all launcher icons for a _Flutter_ project. See also: _How Do I Use It_ at the end of this document

1. Install _envara_ from _PyPI_

2. In a _.py_ file, try the following:

   ```py
   from pathlib import Path
   from envara import Env
   ...
   Env.expand("Home $HOME, arg #1: $1", plain_args)
   ...
   DotEnv.load_from_file(Path('/path/to/.my.env'), default_dir='/home/user/local/bin')
   ```

### How to Expand Environment Variables and Arguments in a String

__*Env.expand (input: str, args: list\[str\] = None, flags: EnvExpandFlags = EnvExpandFlags.DEFAULT) -> str*__

1. A string to expand

   Some string that might contain references to environment variables, user home and/or your application's command-line arguments: _Home ~, Abc: $ABC, arg #1: $1_. For any non-existent environment variable or an index outside the boundaries, the pattern will remain untouched.

2. A list of command-line arguments (optional)

   These could be plain arguments left after parsing command-line options.

3. A bitwise combination of flags listed under the _EnvExpandFlags_ enumeration:

   - _NONE_: none of the below (default)
   - _DECODE\_ESCAPED_: expand escaped characters: _\\\\_, _\\n_, _\\uNNNN_, etc.
   - _REMOVE\_LINE\_COMMENT_: remove hash _#_ (outside the quotes if found) and everything beyond that
   - _REMOVE\_QUOTES_: remove leading and trailing quotes
   - _SKIP\_ENVIRON_: do not expand environment variables
   - _SKIP\_SINGLE\_QUOTED_: if a string is embraced in apostrophes, don't expand it.

4. Directory to locate the default files

   If not specified, the directory of the first parameter will be used (a parent of a file if file, or itself if directory). If the first parameter is not specified either, the current directory will be used.

5. Return value

   A copy of the first parameter expanded as described above.

__*Env.expandargs (input: str, args: list\[str\] = None) -> str*__

1. A string to expand

   Some string that might contain 1-based references to your application's command-line arguments or any other list of strings: _Project Name: $1_. For any index outside the boundaries, the pattern will remain untouched.

2. A list of command-line arguments (optional, although a bit pointless)

   These could be plain arguments left after parsing command-line options.

3. Return value

   A copy of the first parameter expanded as described above.

__*Env.quote (input: str, type: EnvQuoteType = EnvQuoteType.DOUBLE) -> str*__

1. A string to enclose in quotes

   Might contain an escape character _\\_ and/or internal similar quotes, all of those will be escaped with another _\\_.

2. A quote type

   One of the following _EnvQuoteType_ values: _NONE_, _SINGLE_ or _DOUBLE_.

3. Return value

   A copy of the first parameter quoted as per the second argument.

__*Env.remove_line_comment (input: str) -> str*__

1. A string to clean

   For multiline strings, it is highly recommended to split those into a list, then to call this method on each item. You'll process the input line-by-line anyway.

2. Return value

   A copy of the first parameter with everything beyond the first encountered outside string literals hash symbol _#_.

__*Env.unquote (input: str) -> tuple[str, EnvQuoteType]*__

1. A string to remove quotes from

   Might contain escaped characters like _\\t_, _\\n_, _\\uNNNN_, etc., as well as escaped similar quote. All of those will be converted to the respected unescaped characters in case of a double-quoted string. A single-quoted one will remain intact: just the enclosing quotes removed. If the string doesn't start with the expected quote, it will be returned as-is. If no closing quote found, a _ValueError_ will be raised.

2. Return value

   A tuple of the first parameter unquoted, and the type of quotes encountered. This can be used to determine which quotes the string had were before.

### How to Load .env file

__*DotEnv.load\_from\_file(path: Path, file_flags: DotEnvFileFlags, expand_flags: EnvExpandFlags) -> str*__

1. A file or directory

   If file, will be loaded after the default ones (see below), if directory, will be used to locate the default files in, if _None_, the current directory will be used.

2. A bitwise combination of flags:

   - _NONE_: none of the below (default)
   - _RESET_: discard internally accumulated list of loaded files
   - _SKIP\_DEFAULT\_FILES_: do not load any default file
   - _VISIBLE\_FILES_: do not prepend default filenames with a dot

3. Default directory _default\_dir_

   Directory to look for the default files in. If not specified, the directory of the first parameter will be used if passed, or the current directory otherwise.

### The Default .env Files

These files will be loaded in the noted order before the custom one. This happens in _DotEnv.read\_text()_, which is called by _DotEnv.load\_from\_file()_.

The placeholder _system_ is the lowercased value returned by the _platform.system()_ call.

- _[.]env_, then _[.]any.env_

  Always.

- _[.]posix.env_

  When _system_ contains one of the following: _aix_, _bsd_, _darwin_, _linux_, _cygwin_, _java_, _MSYS_.

- _[.]bsd.env_

  When _system_ contains _bsd_ or _darwin_.

- _[.]linux.env_

  When _system_ contains one of the following: _linux_, _cygwin_, _java_, _MSYS_.

- _[.]darwin.env_

  When _system_ contains _darwin_ or _macos_ or _ios_ or _ipados_.

- _[.]macos.env_

  When _system_ contains _darwin_ or _macos_.

- _[.]vms.env_

  When _system_ contains _vms_.

- _[.]windows.env_

  When _system_ starts with _win_.

- _[.]\<system\>.env_

  Always: _\<system\>_ is the actual value of _system_.

### How to Utilise the Stack of Default _.env_ Files

For instance, you are going to call _Google Chrome_ from your script in headless mode to save some screenshots. In that case, you can define variables _ARG\_HEADLESS_ and _CMD\_CHROME_ as follows:

- _.env_:

  PROJECT_NAME=$1 # need to pass a list command-line arguments

  VERSION="${2}_$3"

  ARG_HEADLESS="--headless --disable-gpu --default-background-color=00000000 --window-size={w},{h} --screenshot={o} file://{i}"

- _.linux.env_:

    CMD_CHROME="google-chrome $ARG_HEADLESS"

- _.bsd.env_:

    CMD_CHROME="chrome $ARG_HEADLESS"

- _.macos.env_:

    CMD_CHROME="\\"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome\\" $ARG_HEADLESS"

- _.windows.env_:

    CMD_CHROME="chrome $ARG_HEADLESS"

## __Good Luck!__
