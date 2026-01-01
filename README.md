# envara (C) Alexander Iurovetski 2025

## A library to expand environment variables, program arguments and special characters in a string, as well as parse general and OS-specific .env  files

This library allows to expand environment variables and program arguments in a string, parse general and OS-specific .env  files.

The application does not depend on any special Python package.

### Usage

This example can be used to generate all launcher icons for a _Flutter_ project. See also: _How Do I Use It_ at the end of this document

1. Install _envara_ from _PyPI_

2. In your _.py_ file(s), add the following:

   ```py
   from pathlib import Path
   from envara import Env
   ...
   Env.expand("Home ${HOME:-$USERPROFILE}, arg #1: $1", plain_args)
   ...
   Env.load_from_file(Path('/path/to/.my.env'), with_defaults=True, default_dir='/home/user/local/bin')
   ```

### How to Expand Environment Variables and Arguments in a String

_Env.expand(...)_ has up to 2 arguments:

1. String to expand

   Some string that might contain references to environment variables and/or your application's command-line arguments: `"Home ${HOME:-$USERPROFILE}, arg #1: $1"`

2. A list of commansd-line arguments (optional)

   These could be plain arguments left after parsing command-line options

### How to Load .env file

_Env.load_from_file(...)_ has up to 3 arguments:

1. Path _path_

   Based on your own _.env_ file or directory (the latter will be used to locate the default files), default: current directory.

2. Bool _with_defaults_:

   If True, the method will look for the following default files in the same directory as for the above, and in the incremental order. Makes decision based on the value returned by _platform.system().lower()_. If the respective file is not present, will skip it silently:

   - _.env_

     Use always

   - _.unix.env_

     Use for a UNIX-like: _system_ should contain _aix_ or _bsd_ or _darwin_ or _linux_

   - _.bsd.env_

     Use for a BSD-like: _system_ should contain _bsd_ or _darwin_

   - _linux.env_

     Use for a UNIX-like non-BSD: _system_ should contain _linux_

   - _.darwin.env_

     Use for macOS only: _system_ should contain _darwin_

   - _.vms.env_

     Use for any VMS-compliant system: _system_ should contain _vms_

   - _.windows.env_

     Use for Windows or OS/2 only: _system_ should contain _windows_ or _os2_

3. Path _default_dir_

  Alternative directory to look for the default files in, when specified as relative, will always use the current directory to reslove

If it fails to determine _system_ as above (like _cygwin_, _java_, _MSYS_, etc.), it will analyze the current directory path and make decision based on directory separator character: _unix_, _vms_ or _windows_
  
If you do not specify your own _.env_ file or directory, _with_defaults_ will be considered as _True_, and the default files listed above will be searched in _default_dir_ or in the current directory if the former is omitted too.

## __Good Luck!__
