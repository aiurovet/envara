@echo off

:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:: envara (C) Alexander Iurovetski 2026
::
:: Script to build and upload a given package (command-line argument)
::
:: Requires:
::
::   %USERPROFILE%\.pypirc with the entries [pypi] and [testpypi]
::  pip install build twine
::
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

setlocal enabledelayedexpansion

set "DEST=TestPyPI"
set "IURL=--index-url https://test.pypi.org/simple/"
set "REPO=--repository testpypi"
set "MODE=t"

:parse
if not "%1"=="" (
    if "%1"=="-h" goto usage
    if "%1"=="-r" (
        set "DEST=PyPI"
        set "IURL="
        set "REPO="
        set "MODE=r"
        shift
        goto parse
    )
    if "%1"=="-t" (
        set "MODE=t"
        shift
        goto parse
    )
    set "PROJ=%1"
    shift
    goto parse
)

if "%PROJ%"=="" (
    pushd "%~dp0.." >nul && set "PDIR=%CD%" && popd
    for %%R in ("!PDIR!") do set "PROJ=%%~nxR"
    if "!PROJ!"=="" (
        call :fail "Project name was not specified"
        goto usage
    )
) else (
    set "PDIR=%USERPROFILE%\Projects\%PROJ%"
)

if not exist "%PDIR%" (
    call :fail "Directory not found: %PDIR%"
    goto :eof
)

call :main
goto :eof

:main
call :log "Switching to %PDIR%"
cd /d "%PDIR%"

call :log "Removing old versions"
if exist dist\ rmdir /s /q dist

call :log "Building %PROJ%"
python3 -m build

call :log "Uploading %PROJ% to %DEST%"
python3 -m twine upload %REPO% dist\*

echo.
echo *** Upload successfully completed. To verify, run the following command:
echo.
if not "%IURL%"=="" (
    echo pip install %IURL% %PROJ%
) else (
    echo pip install %PROJ%
)
echo.
goto :eof

:log
echo.
echo *** %~1
echo.
goto :eof

:fail
echo.
echo *** ERROR:
echo.
echo %~1
echo.
exit /b 1

:usage
echo.
echo USAGE:
echo.
echo %~dpn0 OPTIONS project-name
echo.
echo OPTIONS:
echo.
echo -h - this help screen
echo -r - release mode: upload to PyPI, default: upload to TestPyPI
echo.
echo ARGUMENTS:
echo.
echo project-name - your project name: a directory under %%USERPROFILE%%\Projects
echo.
exit /b 1
