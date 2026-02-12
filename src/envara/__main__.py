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

For any platform:
    .env, .env.any, [.]any.env

Android, Linux:
    .env.posix, [.]posix.env
    .env.linux, [.]linux.env
BSD-like:
    .env.posix, [.]posix.env
    .env.bsd, [.]bsd.env
Cygwin, MSYS:
    .env.posix, [.]posix.env
iOS, iPadOS, macOS:
    .env.posix, [.]posix.env
    .env.bsd, [.]bsd.env
    .env.darwin, [.]darwin.env
Java:
    .env.posix, [.]posix.env (on POSIX platforms)
    .env.windows, [.]windows.env (on Windows)
VMS:
    .env.vms, [.]vms.env
Windows:
    .env.windows, [.]windows.env

For any platform again:
    .env.<sys.platform>, [.]<sys.platform>.env

None of these files is required, and will be picked only if found and verified
to be relevant to the platform you are running under. The platform includes not
only OSes, but also Java, Cygwin and MSYS as well as such artefact OSes as AIX,
RiscOS, OpenVMS, OS/2, etc.

This allows you to define extra environment variables to make your application
portable. For instance, you are going to call Google Chrome from your script
in headless mode to save some screenshots. In that case, you can define a
variable CMD_CHROME as follows:

    .env OR .env.any OR.any.env OR any.env:

        APP_NAME = $1 # need to pass a list of command-line arguments
        APP_VERSION = "${2}_$3"
        PROJECT_PATH = ~/Projects/$APP_NAME
        ARG_HEADLESS = "--headless --disable-gpu --default-background-color=00000000 --window-size={w},{h} --screenshot={o} file://{i}"

    .env.linux OR .linux.env OR linux.env:

        CMD_CHROME = "google-chrome $ARG_HEADLESS"

    .env.bsd OR .bsd.env OR bsd.env

       CMD_CHROME = "chrome $ARG_HEADLESS"

    .env.macos OR .macos.env OR macos.env

        CMD_CHROME = "\\\"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome\\\" $ARG_HEADLESS"

    .env.windows

        CMD_CHROME = "chrome $ARG_HEADLESS"
"""
    )

    exit(0)


###############################################################################
