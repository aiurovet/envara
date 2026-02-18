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

A library to expand environment variables, application arguments and escaped
in arbitrary strings, as well as to load stacked dot-env files, remove line
comments, unquote and and expand values as above (if the input was unquoted
or enclosed in single quotes), execute sub-commands, and finally, extend the
environment.

class Env:
    .expand()
    .expand_posix()
    .expand_simple() # Windows-like
    .get_platform_stack()
    .quote()
    .unescape()
    .unquote()
          
class DotEnv:
    .load()
    .load_from_str()
    .read_text()

See README.md for more details about these calls
          
Here is an incomplete list of dot-env files the latter method will look for

Note that the leading dot is optional, except for .env, <sys.platform> gets
lowercased, each file loaded once, unless internal cache is dropped:

== For any filter ==

    .env

== Platforms (added to the list of filters by default) ==

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
to be relevant to the platform you are running under. The platform includes
not only OSes, but also Java, Cygwin and MSYS as well as such artefact OSes as
AIX, RiscOS, OpenVMS, OS/2, etc.

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

== Extra filters ==

You can also pass things like "dev" (runtime environment) or "es" (current
language), as well as a list of all expected runtime environments and a list
of all expected languages. All that will be considered while filtering .env
files in a specified directory. Please note also that if a filename does not
contain an element you are filtering on, it will be considered as common to
the whole subset. For instance, having .env.es will imply it is applicable
to any runtime env, or having .env.test will imply it is applicable to any
selected language when running in "test".

The filterable elements can appear in a filename in any order
"""
    )

    exit(0)


###############################################################################
