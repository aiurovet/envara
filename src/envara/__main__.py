#!/usr/bin/env python3

###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# Main module to present a minimal help
###############################################################################


if __name__ == "__main__":

    print("""

Envara (c) Alexander Iurovetski 2026

A library to expand environment variables, user home, application arguments
and escaped characters in arbitrary strings, as well as to load stacked
dot-env files, remove line comments, unquote and and expand values as above
(if the input was unquoted or enclosed in single quotes), then extend the
environment.

class Env:
    .expand()
    .expandargs()
    .quote()
    .remove_line_comment()
    .unquote()
          
class DotEnv:
    .load_from_file()
    .load_from_str()
    .read_text()

See README.md for more details about these calls
          
Dot-env files the latter method will look for (the leading dot is optional,
each file loaded once):

Any OS:
    [.]env
    [.]any.env
Android, Linux:
    [.]posix.env
    [.]linux.env
    [.]<system>.env
BSD-like:
    [.]posix.env
    [.]bsd.env
    [.]<system>.env
iOS, iPadOS, macOS:
    [.]posix.env
    [.]bsd.env
    [.]darwin.env
    [.]<system>.env
VMS:
    [.]vms.env
    [.]<system>.env (e.g., [.]openvms.env)
Windows, OS/2:
    [.]windows.env
    [.]<system>.env (i.e. [.]win32.env or [.]os2.env)

Where <system> is the lowercased result of platform.system()

None of these files is required, and will be picked only if found and verified
to be relevant to the system you are running under. The system includes not
only OSes, but also Java, Cygwin and MSYS as well as such artefact OSes as AIX,
RiscOS, OpenVMS, OS/2, etc.

This allows you to define extra environment variables to make your application
portable. For instance, you are going to call Google Chrome from your script
in headless mode to save some screenshots. In that case, you can define a
variable CMD_CHROME as follows:

    .env:
        PROJECT_NAME=$1 # need to pass a list command-line arguments
        VERSION="${2}_$3"
        ARG_HEADLESS="--headless --disable-gpu --default-background-color=00000000 --window-size={w},{h} --screenshot={o} file://{i}"
    .linux.env:
        CMD_CHROME="google-chrome $ARG_HEADLESS"
    .bsd.env
        CMD_CHROME="chrome $ARG_HEADLESS"
    .macos.env
        CMD_CHROME="\\\"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome\\\" $ARG_HEADLESS"
    .windows.env
        CMD_CHROME="chrome $ARG_HEADLESS"
""")

    exit(0)


###############################################################################
