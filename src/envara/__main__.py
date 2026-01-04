#!/usr/bin/env python3

###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# Main module to present a minimal help
###############################################################################


if __name__ == "__main__":

    print(
        """

envara (c) Alexander Iurovetski 2026

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
          
Here is an incomplete list of dot-env files the latter method will look for

Note that the leading dot is optional, except for .env, extension can be
changed, <sys.platform> lowercased, each file loaded once:

Any platform:
    .env
    [.]any.env

Android, Linux:
    [.]posix.env
    [.]linux.env
BSD-like:
    [.]posix.env
    [.]bsd.env
Cygwin, MSYS:
    [.]posix.env
iOS, iPadOS, macOS:
    [.]posix.env
    [.]bsd.env
    [.]darwin.env
Java:
    [.]posix.env (on POSIX platforms)
    [.]windows.env (on Windows)
VMS:
    [.]vms.env
Windows:
    [.]windows.env

Any platform again:
    [.]<sys.platform>.env

None of these files is required, and will be picked only if found and verified
to be relevant to the platform you are running under. The platform includes not
only OSes, but also Java, Cygwin and MSYS as well as such artefact OSes as AIX,
RiscOS, OpenVMS, OS/2, etc.

This allows you to define extra environment variables to make your application
portable. For instance, you are going to call Google Chrome from your script
in headless mode to save some screenshots. In that case, you can define a
variable CMD_CHROME as follows:

    .env:
        APP_NAME = $1 # need to pass a list of command-line arguments
        APP_VERSION = "${2}_$3"
        PROJECT_PATH = ~/Projects/$APP_NAME
        ARG_HEADLESS = "--headless --disable-gpu --default-background-color=00000000 --window-size={w},{h} --screenshot={o} file://{i}"
    .linux.env:
        CMD_CHROME = "google-chrome $ARG_HEADLESS"
    .bsd.env
        CMD_CHROME = "chrome $ARG_HEADLESS"
    .macos.env
        CMD_CHROME = "\\\"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome\\\" $ARG_HEADLESS"
    .windows.env
        CMD_CHROME = "chrome $ARG_HEADLESS"
"""
    )

    exit(0)


###############################################################################
