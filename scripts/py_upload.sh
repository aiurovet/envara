#!/bin/sh

###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# Script to build and upload a given package (command-line argument)
#
# Requires:
#
#   ~/.pypirc with the entries [pypi] and [testpypi]
#  pip install build twine
#
###############################################################################

set -Ee

###############################################################################

fail() {
    local msg="$1"

    if [ -n "$msg" ]; then
        printf "\n*** ERROR:\n\n$msg\n\n" >&2
    fi

    exit 1
}

###############################################################################

init() {
    DEST="TestPyPI"
    IURL="--index-url https://test.pypi.org/simple/"
    REPO="--repository testpypi"

    while getopts "hrt" opt; do
        case "$opt" in
            h)
                usage
                ;;
            r)
                DEST="PyPI"
                IURL=""
                PROJ=""
                REPO=""
                ;;
            t)
                ;;
            ?)
                echo "Unknown option -$opt" >&2
                exit 1
                ;;
        esac
    done

    shift $(echo "$OPTIND - 1" | bc)
    PROJ="$1"

    if [ -z "$PROJ" ]; then
        usage "Project name was not specified"
    fi

    PDIR="$HOME/Projects/$PROJ"

    if [ ! -d "$PDIR" ]; then
        fail "Directory not found: \"$PDIR\""
    fi
}

###############################################################################

log() {
    printf "\n*** $1\n\n"
}

###############################################################################

main() {
    init "$@"

    log "Switching to \"$PDIR\""
    cd "$PDIR"

    log "Removing old versions"
    rm -rf dist/*

    log "Building $PROJ"
    python3 -m build

    log "Uploading $PROJ to $DEST"
    python3 -m twine upload $REPO dist/*

    cat <<EOT

*** Upload successfully completed. To verify, run the following command:

pip install $IURL $PROJ

EOT
}

###############################################################################

usage() {
    local msg="$1"
    local app=$(basename $0)

    cat <<EOT

USAGE:

~/Projects/$app OPTIONS project-name

OPTIONS:

-h - this help screen
-r - release mode: upload to PyPI, default: upload to TestPyPI

ARGUMENTS:

project-name - your project name: a directory under $HOME/Projects

EOT

    fail "$msg"
}

###############################################################################

main "$@"

###############################################################################
