#!/usr/bin/env python3

###############################################################################
# svg2many (C) Alexander Iurovetski 2025
#
# Application to export an SVG file to raster image files of multiple sizes
# and optionally, split into background and foreground images
#
# Entry point
#
# See README.md for more details
#
# Build:
#
# cd <project-dir>
# python3 -m build
#
# Upload:
#
# cd <project-dir>
# python3 -m twine upload -r testpypi dist/*
# python3 -m twine upload -r pypi dist/*
###############################################################################

from argparse import Namespace

from svg2many.cli import Cli
from svg2many.config import Config
from svg2many.logger import LogLevel, Logger

###############################################################################


def run(logger: Logger):
    """
    Application start
    """
    try:
        opts, args = parse_args(logger)

        c = Config(__file__, logger)
        c.process_from_file(opts, args)

        return 0
    except Exception as ex:
        logger.err(f"\n*** ERROR: ***\n\n{ex}\n")
        return 1


###############################################################################


def main():
    return run(Logger())


###############################################################################


def parse_args(logger: Logger) -> tuple[Namespace, list[str]]:
    result = Cli.parse()
    opts = result[0]

    logger.level = (
        LogLevel.DBG
        if (opts.verbose)
        else LogLevel.NIL if (opts.quiet) else logger.level
    )

    return result


###############################################################################

if __name__ == "__main__":
    exit(main())

###############################################################################
