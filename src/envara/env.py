###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# A class to expand environment variables, user info (~), arguments from a
# list and escaped characters (\t, \n, etc.) in a string. As well as remove
# line comments if needed
#
# Additionally, accepts bit flags to control what and hopw to expand
#
# This class also allows to avoid unnecessary dependency: easy to implement.
###############################################################################

import os
from pathlib import Path
import re
import string
import sys
import fnmatch
import subprocess
import shlex
from collections.abc import MutableMapping
from typing import ClassVar

from envara.env_chars import EnvChars
from envara.env_chars_data import EnvCharsData
from envara.env_expand_flags import EnvExpandFlags
from envara.env_platform_flags import EnvPlatformFlags
from envara.env_quote_type import EnvQuoteType

###############################################################################


class Env:
    """
    Class for string expansions
    """

    ###########################################################################

    IS_POSIX: ClassVar[bool] = EnvChars.IS_POSIX
    """True if the app is running under Linux, UNIX, BSD, macOS or smimilar"""

    IS_VMS: ClassVar[bool] = EnvChars.IS_VMS
    """True if the app is running under OpenVMS or similar"""

    IS_WINDOWS: ClassVar[bool] = EnvChars.IS_WINDOWS
    """True if the app is running under Windows or OS/2"""

    PLATFORM_POSIX: ClassVar[str] = "posix"
    """A text indicating a POSIX-compatible platform"""

    PLATFORM_WINDOWS: ClassVar[str] = "windows"
    """A text indicating a Windows-compatible platform"""

    PLATFORM_THIS: ClassVar[str] = sys.platform.lower()
    """A text indicating the running platform"""

    SPECIAL: ClassVar[dict[str, str]] = {
        "a": "\a",
        "b": "\b",
        "f": "\f",
        "n": "\n",
        "r": "\r",
        "t": "\t",
        "v": "\v",
    }
    """Rules on how to convert special characters when they
    follow an odd number of escape characters"""

    SPECIAL_CMDSEP_RE: ClassVar[re.Pattern[str]] = re.compile(f"^([&|;]*)(.*?)([&|;]*)$")
    """Special characters' regex for the extra split when no space inserted"""

    SYS_PLATFORM_MAP: ClassVar[dict[str, list[str]]] = {
        "": [PLATFORM_POSIX, PLATFORM_WINDOWS],  # both checked via os.sep
        "^aix": ["aix"],
        "android": ["linux", "android"],
        "^atheos": ["atheos"],
        "^beos|haiku": ["beos", "haiku"],
        "bsd": ["bsd"],
        "cygwin": ["cygwin"],
        "darwin|macos": ["bsd", "darwin", "macos"],
        "^ios|^ipados": ["bsd", "ios"],
        "java": ["java"],
        "^linux": ["linux"],
        "^os2": ["os2"],
        "^msys": ["msys"],
        "vms": ["vms"],
        ".+": [PLATFORM_THIS],
    }
    """Dictionary: regex => list-of-platform-names"""

    ###########################################################################

    @staticmethod
    def expand(
        input: str | None,
        args: list[str] | None = None,
        vars: MutableMapping[str, str] | None = None,
        flags: EnvExpandFlags = EnvExpandFlags.DEFAULT,
        chars: EnvCharsData | None = None,
        subprocess_timeout: float | None = None,
    ) -> str | None:
        """
        Unquote the input if required via flags, remove trailing line comment
        if required via flags, expand the result with the arguments if
        required via flags, expand the result with the environment variables'
        values. The method follows POSIX (in fact, bash) and Windows/OpenVMS
        expansion conventions depending on chars.is_posix and chars.is_windows

        :param input: String to expand
        :type input: str | None

        :param args: List of arguments to expand $#, $1, $2, ...
            pass [] or None to avoid expansion
        :type args: list[str] | None

        :param vars: Dictionary of pairs string => string;
            if None, os.environ will be used; pass {} to avoid expansion
        :type vars: MutableMapping[str, str] | None

        :param flags: Flags controlling what/how to expand input
        :type flags: EnvExpandFlags

        :param chars: Platform-specific special environment characters to
            parse various tokens like escaped characters, environment
            variables, etc.
        :type chars: EnvCharsData

        :param subprocess_timeout: Timeout in seconds for subprocess execution
        :type subprocess_timeout: float | None

        :return: Expanded string
        :rtype: str | None
        """

        if chars is None:
            chars = EnvChars.Current

        # Remove quotes if found and return if empty or None

        result, quote_type = Env.unquote(input, flags=flags, chars=chars)

        if not result:
            return result

        # SKIP_SINGLE_QUOTED prevents any expansion

        if flags & EnvExpandFlags.SKIP_HARD_QUOTED:
            if quote_type == EnvQuoteType.HARD:
                return result

        # Perform expansions depending on the chars's flags

        if chars and chars.is_posix:
            result = Env.__expand_posix(
                result,
                args=args,
                vars=vars,
                flags=flags,
                chars=chars,
                subprocess_timeout=subprocess_timeout,
            )
        else:
            result = Env.__expand_simple(
                result, args=args, vars=vars, flags=flags, chars=chars
            )

        # Perform unescape if requested

        if flags & EnvExpandFlags.UNESCAPE:
            result = Env.unescape(str(result), chars=chars)

        # Return final result

        return result

    ###########################################################################

    @staticmethod
    def expand_path(
        path: Path | None,
        args: list[str] | None = None,
        vars: MutableMapping[str, str] | None = None,
        flags: EnvExpandFlags = EnvExpandFlags.DEFAULT,
        chars: EnvCharsData | None = None,
    ) -> Path | None:
        """
        A wrapper around expand() for paths. It also expands the current or
        specific user's directory according to the current OS's rules
        """
        if chars is None:
            chars = EnvChars.Current

        if not path:
            return path

        input, quote_type = Env.strip(str(path), flags=flags, chars=chars)
        result = Env.expand(input=input, args=args, vars=vars, flags=flags, chars=chars)

        if not result:
            return None

        path = Path(result)

        if quote_type != EnvQuoteType.HARD:
            path = path.expanduser()

        return path

    ###########################################################################
    # This code was mainly generated using Copilot
    ###########################################################################

    @staticmethod
    def __expand_posix(
        input: str | None,
        args: list[str] | None = None,
        vars: MutableMapping[str, str] | None = None,
        flags: EnvExpandFlags = EnvExpandFlags.DEFAULT,
        chars: EnvCharsData | None = None,
        subprocess_timeout: float | None = None,
    ) -> str | None:
        """
        Expand environment variables and sub-processes according to complex
        POSIX (in fact, bash) rules: like ${ABC:-${DEF:-$(uname -a)}. See the
        description of arguments under the main method expand(...)
        """
        if chars is None:
            chars = EnvChars.Current

        if input is None:
            return input

        if vars is None:
            vars = os.environ

        allow_shell = (flags & EnvExpandFlags.ALLOW_SHELL) != 0

        allow_subprocess = allow_shell or ((flags & EnvExpandFlags.ALLOW_SUBPROC) != 0)

        s = input
        res: list[str] = []
        i = 0
        inp_len = len(s)
        bktick = "`"
        is_bktick_cmd = bktick != chars.escape

        expand_char = chars.expand
        escape_char = chars.escape

        def eval_braced(inner: str) -> str:
            # Length: ${#NAME}
            if inner.startswith("#"):
                name = inner[1:]
                val = vars.get(name)
                if val is None:
                    return f"{expand_char}{{{inner}}}"
                return str(len(val))

            # Parse name
            m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)", inner)
            if not m:
                # Support numeric positional parameters inside braces: ${1}, ${2}
                md = re.match(r"^(\d+)", inner)
                if md:
                    name = md.group(1)
                    rest = inner[md.end() :]
                    idx = int(name) - 1
                    if args and 0 <= idx < len(args):
                        val = args[idx]
                        is_set = True
                        is_null = val == ""
                    else:
                        val = None
                        is_set = False
                        is_null = False
                else:
                    return f"{expand_char}{{{inner}}}"
            else:
                name = m.group(1)
                rest = inner[m.end() :]
                val = vars.get(name)
                is_set = val is not None
                is_null = (val == "") if is_set else False

            # Substring: :offset[:length]
            sm = re.match(r"^:(-?\d+)(?::(-?\d+))?$", rest)
            if sm:
                offset = int(sm.group(1))
                length = int(sm.group(2)) if sm.group(2) is not None else None
                if not is_set:
                    return f"{expand_char}{{{inner}}}"
                text = val or ""
                if offset < 0:
                    offset = len(text) + offset
                    if offset < 0:
                        offset = 0
                if length is None:
                    return text[offset:]
                return text[offset : offset + length]

            # Parameter expansion operators
            if rest.startswith(":=") or rest.startswith("="):
                assign_colon = rest.startswith(":=")
                word = rest[2:] if assign_colon else rest[1:]
                if (not is_set) or (assign_colon and is_null):
                    new_val = str(
                        Env.__expand_posix(
                            word,
                            args=args,
                            vars=vars,
                            flags=flags,
                            chars=chars,
                            subprocess_timeout=subprocess_timeout,
                        )
                        or ""
                    )
                    try:
                        vars[name] = new_val
                    except Exception:
                        pass
                    if name.isdigit() and args is not None:
                        arg_idx = int(name) - 1
                        while len(args) <= arg_idx:
                            args.append("")
                        args[arg_idx] = new_val
                    return new_val
                return val or ""

            # Pattern removals: #, ## (prefix) and %, %% (suffix)
            if rest.startswith("##") or rest.startswith("#"):
                pattern = rest[2:] if rest.startswith("##") else rest[1:]
                if not is_set:
                    return f"{expand_char}{{{inner}}}"
                text = val or ""
                best_i = None
                for i in range(0, len(text) + 1):
                    if fnmatch.fnmatchcase(text[0:i], pattern):
                        if rest.startswith("##"):
                            best_i = i
                        else:
                            best_i = i
                            break
                if best_i is None:
                    return text
                return text[best_i:]
            if rest.startswith("%%") or rest.startswith("%"):
                pattern = rest[2:] if rest.startswith("%%") else rest[1:]
                if not is_set:
                    return f"{expand_char}{{{inner}}}"
                text = val or ""
                best_i = None
                for i in range(0, len(text) + 1):
                    sub = text[len(text) - i :]
                    if fnmatch.fnmatchcase(sub, pattern):
                        if rest.startswith("%%"):
                            best_i = i
                        else:
                            best_i = i
                            break
                if best_i is None:
                    return text
                return text[: len(text) - best_i]

            # Substitutions
            anchor = None
            r = rest
            if r and r[0] in ("#", "%"):  # pragma: no cover
                anchor = r[0]
                r = r[1:]

            pat = None
            repl = None
            is_all = False

            if r.startswith("//"):
                is_all = True
                part = r[2:]
                if "/" in part:
                    pat, repl = part.split("/", 1)
            elif r.startswith("/"):
                part = r[1:]
                if "/" in part:
                    pat, repl = part.split("/", 1)
            elif "/" in r:
                pat, repl = r.split("/", 1)

            if pat and pat[0] in ("#", "%"):
                anchor = pat[0]
                pat = pat[1:]

            if (pat is None) or (repl is None):
                pass
            else:
                if not is_set:
                    return f"{expand_char}{{{inner}}}"

                core = fnmatch.translate(pat)
                if core.startswith("(?s:"):
                    if core.endswith(")\\Z") or core.endswith(")\\z"):
                        core = core[4:-3]

                repl_eval = str(
                    Env.__expand_posix(
                        repl,
                        args=args,
                        vars=vars,
                        flags=flags,
                        chars=chars,
                        subprocess_timeout=subprocess_timeout,
                    )
                )

                if anchor == "#":
                    text = val or ""
                    if is_all:
                        while True:
                            changed = False
                            for i in range(1, len(text) + 1):
                                if fnmatch.fnmatchcase(text[:i], pat):
                                    new_text = repl_eval + text[i:]
                                    if new_text == text:
                                        changed = False
                                        break
                                    text = new_text
                                    changed = True
                                    break
                            if not changed:
                                break
                        return text
                    else:
                        for i in range(1, len(text) + 1):
                            if fnmatch.fnmatchcase(text[:i], pat):
                                return repl_eval + text[i:]
                        return val or ""

                if anchor == "%":
                    text = val or ""
                    if is_all:
                        while True:
                            changed = False
                            for i in range(1, len(text) + 1):
                                sub = text[len(text) - i :]
                                if fnmatch.fnmatchcase(sub, pat):
                                    new_text = text[: len(text) - i] + repl_eval
                                    if new_text == text:
                                        changed = False
                                        break
                                    text = new_text
                                    changed = True
                                    break
                            if not changed:
                                break
                        return text
                    else:
                        for i in range(1, len(text) + 1):
                            sub = text[len(text) - i :]
                            if fnmatch.fnmatchcase(sub, pat):
                                return text[: len(text) - i] + repl_eval
                        return val or ""

                pattern = core
                prog = re.compile(pattern, re.DOTALL)
                val = val or ""
                if is_all:
                    return prog.sub(repl_eval, val)
                else:
                    return prog.sub(repl_eval, val, count=1)

            if rest.startswith(":-"):
                word = rest[2:]
                if (not is_set) or is_null:
                    return str(
                        Env.__expand_posix(
                            word,
                            args=args,
                            vars=vars,
                            flags=flags,
                            chars=chars,
                            subprocess_timeout=subprocess_timeout,
                        )
                    )
                return val or ""
            if rest.startswith("-"):
                word = rest[1:]
                if not is_set:
                    return str(
                        Env.__expand_posix(
                            word,
                            args=args,
                            vars=vars,
                            flags=flags,
                            chars=chars,
                            subprocess_timeout=subprocess_timeout,
                        )
                    )
                return val or ""
            if rest.startswith(":+"):
                word = rest[2:]
                if is_set and not is_null:
                    return str(
                        Env.__expand_posix(
                            word,
                            args=args,
                            vars=vars,
                            flags=flags,
                            chars=chars,
                            subprocess_timeout=subprocess_timeout,
                        )
                    )
                return ""
            if rest.startswith("+"):
                word = rest[1:]
                if is_set:
                    return str(
                        Env.__expand_posix(
                            word,
                            args=args,
                            vars=vars,
                            flags=flags,
                            chars=chars,
                            subprocess_timeout=subprocess_timeout,
                        )
                    )
                return ""
            if rest.startswith(":?"):
                word = rest[2:]
                if (not is_set) or is_null:
                    raise ValueError(
                        str(
                            Env.__expand_posix(
                                word,
                                args=args,
                                vars=vars,
                                flags=flags,
                                chars=chars,
                                subprocess_timeout=subprocess_timeout,
                            )
                        )
                        or f"{name}: parameter null or not set"
                    )
                return val or ""
            if rest.startswith("?"):
                word = rest[1:]
                if not is_set:
                    raise ValueError(
                        str(
                            Env.__expand_posix(
                                word,
                                args=args,
                                vars=vars,
                                flags=flags,
                                chars=chars,
                                subprocess_timeout=subprocess_timeout,
                            )
                        )
                        or f"{name}: parameter not set"
                    )
                return val or ""

            # Case modification: ^, ^^, ,, ,, ~, ~~
            # ${var^} - uppercase first character
            # ${var^^} - uppercase all characters
            # ${var,} - lowercase first character
            # ${var,,} - lowercase all characters
            # ${var~} - toggle case of first character
            # ${var~~} - toggle case of all characters
            if rest.startswith("^^"):
                pattern = rest[2:] if len(rest) > 2 else None
                if val is None:
                    return f"{expand_char}{{{inner}}}"
                text = val
                if pattern:
                    # Uppercase all characters matching pattern
                    result = ""
                    for ch in text:
                        if fnmatch.fnmatchcase(ch, pattern):
                            result += ch.upper()
                        else:
                            result += ch
                    return result
                return text.upper()
            if rest.startswith("^"):
                pattern = rest[1:] if len(rest) > 1 else None
                if val is None:
                    return f"{expand_char}{{{inner}}}"
                text = val
                if pattern:
                    # Uppercase first character if it matches pattern
                    if text and fnmatch.fnmatchcase(text[0], pattern):
                        return text[0].upper() + text[1:]
                    return text
                if text:
                    return text[0].upper() + text[1:]
                return text
            if rest.startswith(",,"):
                pattern = rest[2:] if len(rest) > 2 else None
                if val is None:
                    return f"{expand_char}{{{inner}}}"
                text = val
                if pattern:
                    # Lowercase all characters matching pattern
                    result = ""
                    for ch in text:
                        if fnmatch.fnmatchcase(ch, pattern):
                            result += ch.lower()
                        else:
                            result += ch
                    return result
                return text.lower()
            if rest.startswith(","):
                pattern = rest[1:] if len(rest) > 1 else None
                if val is None:
                    return f"{expand_char}{{{inner}}}"
                text = val
                if pattern:
                    # Lowercase first character if it matches pattern
                    if text and fnmatch.fnmatchcase(text[0], pattern):
                        return text[0].lower() + text[1:]
                    return text
                if text:
                    return text[0].lower() + text[1:]
                return text
            if rest.startswith("~~"):
                if val is None:
                    return f"{expand_char}{{{inner}}}"
                text = val
                return text.swapcase()
            if rest.startswith("~"):
                if val is None:
                    return f"{expand_char}{{{inner}}}"
                text = val
                if text:
                    return text[0].swapcase() + text[1:]
                return text

            if is_set:
                return val or ""
            return f"{expand_char}{{{inner}}}"

        while i < inp_len:
            ch = s[i]

            if ch == escape_char:
                j = i
                while j < inp_len and s[j] == escape_char:
                    j += 1
                escape_count = j - i
                if (j < inp_len) and (
                    (s[j] == expand_char) or (is_bktick_cmd and (s[j] == bktick))
                ):
                    res.append(escape_char * (escape_count // 2))
                    if (escape_count % 2) == 1:
                        res.append(s[j])
                        i = j + 1
                        continue
                    i = j
                    continue
                else:
                    res.append(escape_char * escape_count)
                    i = j
                    continue

            if is_bktick_cmd and (ch == bktick):
                j = i + 1
                while j < inp_len:
                    if s[j] == bktick:
                        break
                    if s[j] == escape_char and (j + 1) < inp_len and s[j + 1] == bktick:
                        j += 2
                        continue
                    j += 1
                if j >= inp_len:
                    raise ValueError(
                        f"Unterminated backtick command substitution in: {input}"
                    )
                inner = s[i + 1 : j]
                cmd = (
                    Env.__expand_posix(
                        inner,
                        args=args,
                        vars=vars,
                        flags=flags,
                        chars=chars,
                        subprocess_timeout=subprocess_timeout,
                    )
                    or ""
                )
                if not allow_subprocess:
                    res.append(s[i : j + 1])
                    i = j + 1
                    continue
                try:
                    if allow_shell:
                        proc = subprocess.run(
                            cmd,
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            timeout=subprocess_timeout,
                        )
                    else:
                        proc = subprocess.run(
                            shlex.split(cmd),
                            shell=False,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            timeout=subprocess_timeout,
                        )
                except subprocess.TimeoutExpired:
                    raise ValueError(f"Command substitution timed out: {cmd}")
                if proc.returncode != 0:
                    raise ValueError(
                        f"Command substitution failed: {cmd}: {proc.stderr.strip()}"
                    )
                out = proc.stdout.rstrip("\n")
                res.append(out)
                i = j + 1
                continue

            if ch != expand_char:
                res.append(ch)
                i += 1
                continue

            if (i + 1) < inp_len and s[i + 1] == expand_char:
                res.append(str(os.getpid()))
                i += 2
                continue

            if (i + 1) < inp_len and s[i + 1] == "#":
                if args:
                    res.append(str(len(args)))
                else:
                    res.append("0")
                i += 2
                continue

            if (i + 1) < inp_len and s[i + 1] == "(":
                j = i + 2
                depth = 1
                while j < inp_len:
                    if s[j] == "(":
                        depth += 1
                    elif s[j] == ")":
                        depth -= 1
                        if depth == 0:
                            break
                    j += 1
                if j >= inp_len:
                    raise ValueError(f"Unterminated command substitution in: {input}")
                inner = s[i + 2 : j]
                cmd = (
                    Env.__expand_posix(
                        inner,
                        args=args,
                        vars=vars,
                        flags=flags,
                        chars=chars,
                        subprocess_timeout=subprocess_timeout,
                    )
                    or ""
                )
                if not allow_subprocess:
                    res.append(s[i : j + 1])
                    i = j + 1
                    continue
                try:
                    if allow_shell:
                        proc = subprocess.run(
                            cmd,
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            timeout=subprocess_timeout,
                        )
                    else:
                        proc = subprocess.run(
                            shlex.split(cmd),
                            shell=False,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            timeout=subprocess_timeout,
                        )
                except subprocess.TimeoutExpired:
                    raise ValueError(f"Command substitution timed out: {cmd}")
                if proc.returncode != 0:
                    raise ValueError(
                        f"Command substitution failed: {cmd}: {proc.stderr.strip()}"
                    )
                out = proc.stdout.rstrip("\n")
                res.append(out)
                i = j + 1
                continue

            if (i + 1) < inp_len and s[i + 1] == "{":
                j = i + 2
                depth = 1
                while j < inp_len:
                    if s[j] == "{":
                        depth += 1
                    elif s[j] == "}":
                        depth -= 1
                        if depth == 0:
                            break
                    j += 1
                if j >= inp_len:
                    raise ValueError(f"Unterminated braced expansion in: {input}")
                inner = s[i + 2 : j]
                res.append(eval_braced(inner))
                i = j + 1
                continue

            j = i + 1
            if j < inp_len:
                ch2 = s[j]
                if ch2.isdigit():
                    start = j
                    while j < inp_len and s[j].isdigit():
                        j += 1
                    idx = int(s[start:j]) - 1
                    if args and 0 <= idx < len(args):
                        res.append(args[idx])
                    else:
                        res.append(s[i:j])
                    i = j
                    continue

                if ch2.isalpha() or ch2 == "_":
                    start = j
                    while j < inp_len and (s[j].isalnum() or s[j] == "_"):
                        j += 1
                    name = s[start:j]
                    val = vars.get(name)
                    if val is None:
                        res.append(s[i:j])
                    else:
                        res.append(val)
                    i = j
                    continue

            res.append(expand_char)
            i += 1

        result = "".join(res)

        return result

    ###########################################################################
    # This code was mainly generated using Copilot
    ###########################################################################

    @staticmethod
    def __expand_simple(
        input: str | None,
        args: list[str] | None = None,
        vars: MutableMapping[str, str] | None = None,
        flags: EnvExpandFlags = EnvExpandFlags.DEFAULT,
        chars: EnvCharsData | None = None,
    ) -> str | None:
        """
        Expand environment variables and sub-processes according to simple
        rules and symmetric expand characters: like %ABC% in Windows. See
        the description of arguments under the main method expand(...)
        """
        if chars is None:
            chars = EnvChars.Current

        if input is None:
            return input

        is_path = isinstance(input, Path)

        if vars is None:
            vars = os.environ

        expand_char = chars.expand
        windup_char = chars.windup
        escape_char = chars.escape
        is_windows = chars.is_windows

        s = str(input) if is_path else input
        i = 0
        ln = len(s)
        out: list[str] = []

        while i < ln:
            ch = s[i]

            if ch == escape_char:
                if (i + 1) < ln:
                    nxt = s[i + 1]
                    if nxt == expand_char:
                        if (i + 2) < ln and s[i + 2] == expand_char:
                            out.append(expand_char)
                            i += 3
                            continue
                        if (i + 2) < ln and s[i + 2].isdigit():
                            j = i + 2
                            while j < ln and s[j].isdigit():
                                j += 1
                            out.append(expand_char + s[i + 2 : j])
                            i = j
                            continue
                        k = s.find(windup_char, i + 2)
                        if k != -1:
                            out.append(s[i + 1 : k + 1])
                            i = k + 1
                            continue
                        out.append(expand_char)
                        i += 2
                        continue
                    out.append(ch)
                    out.append(nxt)
                    i += 2
                    continue
                else:
                    out.append(escape_char)
                    i += 1
                    continue

            if ch != expand_char:
                out.append(ch)
                i += 1
                continue

            if (i + 1) < ln and s[i + 1] == windup_char:
                out.append(expand_char)
                i += 2
                continue

            j = i + 1

            if is_windows:
                if j < ln and s[j] == "~":
                    k = j + 1
                    mods: list[str] = []
                    while k < ln and s[k].isalpha():
                        mods.append(s[k])
                        k += 1
                    if k < ln and s[k].isdigit():
                        start = k
                        while k < ln and s[k].isdigit():
                            k += 1
                        token = s[start:k]
                        end_with_windup = False
                        if k < ln and s[k] == windup_char:
                            end_with_windup = True
                            k += 1

                        idx = int(token) - 1
                        if args and 0 <= idx < len(args):
                            tokval = args[idx]

                            def part_drive(t: str) -> str:
                                return os.path.splitdrive(t)[0]

                            def part_path(t: str) -> str:
                                p = os.path.dirname(t)
                                if p and not p.endswith(os.sep):
                                    p = p + os.sep
                                return p

                            def part_name(t: str) -> str:
                                return os.path.splitext(os.path.basename(t))[0]

                            def part_ext(t: str) -> str:
                                return os.path.splitext(t)[1]

                            def part_full(t: str) -> str:
                                return os.path.abspath(t)

                            out_frag: list[str] = []
                            for m in mods:
                                if m == "d":
                                    out_frag.append(part_drive(tokval))
                                elif m == "p":
                                    out_frag.append(part_path(tokval))
                                elif m == "n":
                                    out_frag.append(part_name(tokval))
                                elif m == "x":
                                    out_frag.append(part_ext(tokval))
                                elif m == "f":
                                    out_frag.append(part_full(tokval))
                                else:
                                    pass
                            out.append("".join(out_frag))
                        else:
                            if end_with_windup:
                                out.append(expand_char + s[j:k] + windup_char)
                            else:
                                out.append(expand_char + s[j:k])
                        i = k
                        continue

                if j < ln and s[j].isdigit():
                    start = j
                    while j < ln and s[j].isdigit():
                        j += 1
                    end_with_windup = False
                    if j < ln and s[j] == windup_char:
                        end_with_windup = True
                        token = s[start:j]
                        j += 1
                    else:
                        token = s[start:j]

                    idx = int(token) - 1
                    if args and 0 <= idx < len(args):
                        out.append(args[idx])
                    else:
                        if end_with_windup:
                            out.append(expand_char + token + windup_char)
                        else:
                            out.append(expand_char + token)
                    i = j
                    continue

                if j < ln and s[j] == "*":
                    j += 1
                    if j < ln and s[j] == windup_char:
                        j += 1
                    if args:
                        out.append(" ".join(args))
                    else:
                        out.append(expand_char + "*")
                    i = j
                    continue

            k = s.find(windup_char, j)
            if k == -1:
                out.append(expand_char)
                i += 1
                continue

            token = s[j:k]
            if not token:
                out.append(expand_char)
                out.append(windup_char)
                i = k + 1
                continue

            if is_windows and (":~" in token):
                base, suff = token.split(":~", 1)
                if not base:
                    out.append(expand_char + token + windup_char)
                    i = k + 1
                    continue
                if "," in suff:
                    start_str, length_str = suff.split(",", 1)
                else:
                    start_str = suff
                    length_str = None
                try:
                    start = int(start_str)
                    length = (
                        int(length_str)
                        if (length_str is not None and length_str != "")
                        else None
                    )
                except Exception:
                    out.append(expand_char + token + windup_char)
                    i = k + 1
                    continue

                val = vars.get(base)
                if val is None:
                    out.append(expand_char + token + windup_char)
                    i = k + 1
                    continue

                text = val
                if start < 0:
                    start = len(text) + start
                    if start < 0:
                        start = 0
                if length is None:
                    substr = text[start:]
                else:
                    if length < 0:
                        substr = ""
                    else:
                        substr = text[start : start + length]
                out.append(substr)
                i = k + 1
                continue

            name = token
            val = vars.get(name)
            if val is None:
                out.append(expand_char + name + windup_char)
            else:
                out.append(val)

            i = k + 1

        result = "".join(out)

        return result

    ###########################################################################

    @staticmethod
    def get_all_platforms(
        flags: EnvPlatformFlags = EnvPlatformFlags.NONE,
    ) -> list[str]:
        """
        Get the list of all supported platforms (see Env.__platform_map).

        :param flags: Controls which items will be added to the stack
        :type flags: EnvPlatformFlags

        :return: List of all relevant platforms
        :rtype: list[str]
        """

        # Initialize the return value

        result: list[str] = []

        # Add default platform if needed

        if flags & EnvPlatformFlags.ADD_EMPTY:
            result.append("")

        # Traverse the lists of platforms and append distinct

        for platforms in Env.SYS_PLATFORM_MAP.values():
            for platform in platforms:
                if platform not in result:
                    result.append(platform)

        # Return the accumulated list

        return result

    ###########################################################################

    @staticmethod
    def get_cur_platforms(flags: EnvPlatformFlags = EnvPlatformFlags.NONE) -> list[str]:
        """
        Get the list of platforms from more generic to more specific ones.
        For instance, if an application is running on Linux, it could be
        ["posix", "linux", Env.PLATFORM_THIS], or for macOS it could be
        ["posix", "bsd", "darwin", "macos", Env.PLATFORM_THIS]. The last
        item will be added only if more specific than "macOS". An empty
        string is added first to the returned list if you set the
        EnvPlatformFlags.ADD_EMPTY bit in flags.

        :param flags: Controls which items will be added to the list
        :type flags: EnvPlatformFlags

        :return: List of all relevant platforms
        :rtype: list[str]
        """

        # Initialize the return value

        result: list[str] = []

        if flags & EnvPlatformFlags.ADD_EMPTY:
            result.append("")

        # Traverse the {pattern: list-of-relevant-platforms} dictionary and
        # append those where the pattern matches the running platform

        re_flags = re.IGNORECASE | re.UNICODE

        for pattern, platforms in Env.SYS_PLATFORM_MAP.items():
            # If the platform doesn't match the running one, skip it

            if pattern:
                if not re.search(pattern, Env.PLATFORM_THIS, re_flags):
                    continue

            # Append every platform from the current list if eligible

            for platform in platforms:
                # Perform extra checks, platform is never empty or None

                if platform == Env.PLATFORM_POSIX:
                    if not Env.IS_POSIX:
                        continue
                elif platform == Env.PLATFORM_WINDOWS:
                    if not Env.IS_WINDOWS:
                        continue

                # If the platform name was not added yet, add it

                if platform not in result:
                    result.append(platform)

        # Return the accumulated list

        return result

    ###########################################################################

    @staticmethod
    def quote(
        input: str,
        is_forced: bool = False,
        chars: EnvCharsData | None = None,
    ) -> str:
        """
        Enclose input in quotes. Neither leading, nor trailing whitespaces
        removed before checking the leading quotes. Use .strip() yourself
        before calling this method if needed.

        :param input: String being expanded
        :type input: str

        :param is_forced: If True, enclose in quotes even if already quoted
        :type is_forced: bool

        :param chars: Platform-specific special environment characters to
            parse various tokens like escaped characters, environment
            variables, etc.
        :type chars: EnvCharsData

        :return: Quoted string with possible quotes and escape characters from
                 the inside being escaped
        :rtype: str
        """

        if chars is None:
            chars = EnvChars.Current

        # Check empty

        if not input:
            return input

        # Define the quote being used, and if it is empty, return

        quote = chars.normal_quote

        if not quote:
            return input

        # Initialise

        result = input
        length = len(result)

        beg_chr = result[0]
        end_chr = result[length - 1]

        # Get the escape and hard-quote characters to use

        esc = chars.escape
        hard_quote = chars.hard_quote

        # If quoting is not forced, and hard or normal quote is around already,
        # or no space found, return as is

        if not is_forced:
            if (beg_chr == quote) or (beg_chr == hard_quote):
                if (length > 1) and (end_chr == beg_chr):
                    return result
            elif (" " not in result) and (quote not in result):
                if (not hard_quote) or (hard_quote not in result):
                    if (not esc) or (esc not in result):
                        return result

        # If input is not empty, escape the escape character, then the
        # internal quote(s), then embrace the result in desired quotes
        # and return

        if esc in result:
            result = result.replace(esc, f"{esc}{esc}")
        if quote in result:
            result = result.replace(quote, f"{esc}{quote}")

        return f"{quote}{result}{quote}"

    ###########################################################################

    @staticmethod
    def split(
        input: str | None,
        args: list[str] | None = None,
        vars: MutableMapping[str, str] | None = None,
        flags: EnvExpandFlags = EnvExpandFlags.DEFAULT,
        chars: EnvCharsData | None = None,
    ) -> list[str]:
        """
        Split input into tokens following platform-independent command-line
        rules: based on the normal and the hard quotes (if the latter defined)

        :param input: String to split
        :type input: str | None

        :param args: List of arguments to expand $#, $1, $2, ...
            pass [] or None to avoid expansion
        :type args: list[str] | None

        :param vars: Dictionary of pairs string => string;
            if None, os.environ will be used; pass {} to avoid expansion
        :type vars: MutableMapping[str, str] | None

        :param flags: Flags controlling what/how to expand tokens
        :type flags: EnvExpandFlags

        :param chars: Platform-specific special environment characters to
            parse various tokens like escaped characters, environment
            variables, etc.
        :type chars: EnvCharsData

        :return: List of tokens
        :rtype: list[str]
        """
        if chars is None:
            chars = EnvChars.Current

        # If the input is empty or None, return empty list

        if not input:
            return []

        # Simplify special characters

        escape = chars.escape
        normal_quote = chars.normal_quote
        hard_quote = chars.hard_quote

        def add_token_and_reset(
            result: list[str],
            token: list[str],
            args: list[str] | None = None,
            vars: MutableMapping[str, str] | None = None,
            flags: EnvExpandFlags = EnvExpandFlags.DEFAULT,
        ) -> bool:
            tokstr = "".join(token)
            token.clear()
            if chars.cutter and tokstr.startswith(chars.cutter):
                return False
            tokstr = Env.expand(tokstr, args=args, vars=vars, flags=flags, chars=chars)
            if tokstr:
                result += Env.SPECIAL_CMDSEP_RE.sub(r"\1\n\2\n\3", tokstr).split("\n")
            return True

        # Define cumulative lists

        result: list[str] = []
        token: list[str] = []

        # Define local flags and special characters

        in_token = False
        is_escaped = False
        is_ready = False
        quote = None

        # Loop through every character from the input, accumulate current token
        # and append when it ends, then restart anew

        for ch in input:
            if is_ready:
                is_escaped = False
                is_ready = False
                in_token = False
                quote = None

                if len(token) > 0:
                    if not add_token_and_reset(
                        result=result,
                        token=token,
                        args=args,
                        vars=vars,
                        flags=flags,
                    ):
                        break

            if is_escaped:
                token.append(ch)
                is_escaped = False
                continue

            if quote is None:
                if ch == escape:
                    is_escaped = True
                elif (ch == normal_quote) or (ch == hard_quote):
                    if in_token:
                        quote = None
                        in_token = False
                    else:
                        quote = ch
                        in_token = True
                elif ch in string.whitespace:
                    is_ready = in_token
            elif quote == normal_quote:
                if ch == escape:
                    is_escaped = True
                elif ch == quote:
                    is_ready = True
            elif hard_quote and (quote == hard_quote):  # pragma: no cover
                if ch == quote:
                    is_ready = True

            if ((not in_token) or not quote) and (ch in string.whitespace):
                is_ready = True
                continue

            token.append(ch)
            in_token = True

        # If the last token wasn't appended yet, ensure there is no
        # unterminated sequence, then append it

        if len(token) > 0:
            if is_escaped:
                raise ValueError(f"Unterminated escape sequence in: {input}")

            if (quote is not None) and (input[-1] != quote):
                raise ValueError(
                    f"Unterminated {'hard-' if quote == hard_quote else ''}quoted argument in: {input}"
                )

            add_token_and_reset(
                result=result,
                token=token,
                args=args,
                vars=vars,
                flags=flags,
            )

        return result

    ###########################################################################

    @staticmethod
    def strip(
        input: str | None,
        flags: EnvExpandFlags = EnvExpandFlags.DEFAULT,
        chars: EnvCharsData | None = None,
    ) -> tuple[str | None, EnvQuoteType]:
        """
        Remove leading and trailing spaces, then determine the quote type by
        checking the first character.

        :param input: String to remove enclosing quotes from
        :type input: str | None

        :param flags: Flags controlling what/how to unquote input. Essentially,
            only two bits are considered: STRIP_SPACES and STRIP_COMMENT
        :type flags: EnvExpandFlags

        :param chars: Platform-specific special environment characters to
            parse various tokens like escaped characters, environment
            variables, etc.
        :type chars: EnvCharsData

        :return: input stripped off leading and trailing spaces and the type
            of surrounding quotes if found
        :rtype: tuple[str | None, EnvQuoteType]
        """

        if chars is None:
            chars = EnvChars.Current

        if not input:
            return (input, EnvQuoteType.NONE)

        strip_spaces = (flags & EnvExpandFlags.STRIP_SPACES) != 0
        result = input.strip() if (strip_spaces) else input

        if not result:
            return (result, EnvQuoteType.NONE)

        if chars.hard_quote and result.startswith(chars.hard_quote):
            return (result, EnvQuoteType.HARD)

        if chars.normal_quote and result.startswith(chars.normal_quote):
            return (result, EnvQuoteType.NORMAL)

        return (result, EnvQuoteType.NONE)

    ###########################################################################

    @staticmethod
    def unescape(
        input: str, strip_blanks: bool = False, chars: EnvCharsData | None = None
    ) -> str:
        """
        Unescape '\\t', '\\n', '\\u0022' etc.

        :param input: Input string to unescape escaped characters in
        :type input: str

        :param strip_blanks: True = remove leading and trailing blanks
        :type strip_blanks: bool

        :param chars: Platform-specific special environment characters to
            parse various tokens like escaped characters, environment
            variables, etc.
        :type chars: EnvCharsData

        :return: Unescaped string, optionally, stripped of blanks
        :rtype: str
        """

        if chars is None:
            chars = EnvChars.Current

        # If input is void, return empty string

        if not input:
            return ""

        # If escape character is empty or if the input does not contain it,
        # then finish

        if (not chars.escape) or chars.escape not in input:
            return input

        # Loop through the input and accumulate valid characters in chr_lst

        chr_lst: list[str] = []
        cur_pos = -1
        esc_pos = -1
        is_escaped = False

        # Start and end of a substring to accumulate for the code-to-string
        # conversion

        acc_beg_pos = -1
        acc_end_pos = -1

        for cur_char in input:
            cur_pos = cur_pos + 1

            if (cur_pos >= acc_beg_pos) and (cur_pos < acc_end_pos):
                if cur_char not in string.hexdigits:
                    Env.__fail_unescape(input, esc_pos, cur_pos)
                continue

            if cur_pos == acc_end_pos:
                chr_lst.append(chr(int(input[acc_beg_pos:acc_end_pos], 16)))
                is_escaped = False

            if is_escaped:
                if cur_char in Env.SPECIAL:
                    cur_char = Env.SPECIAL[cur_char]
                elif cur_char == "u":
                    acc_beg_pos = cur_pos + 1
                    acc_end_pos = acc_beg_pos + 4
                    continue
                elif cur_char == "x":
                    acc_beg_pos = cur_pos + 1
                    acc_end_pos = acc_beg_pos + 2
                    continue
                is_escaped = False
            elif cur_char == chars.escape:
                is_escaped = not is_escaped
                esc_pos = cur_pos if (is_escaped) else -1
                continue

            chr_lst.append(cur_char)

        # If escaped char (by code) is the last one, accumulation
        # action was missed from the loop: fulfilling here

        if is_escaped:
            if acc_end_pos > 0:
                if cur_pos >= acc_end_pos - 1:
                    chr_lst.append(chr(int(input[acc_beg_pos:acc_end_pos], 16)))
                elif esc_pos >= 0:  # pragma: no cover
                    Env.__fail_unescape(input, esc_pos, cur_pos + 1)
            elif esc_pos >= 0:  # pragma: no cover
                Env.__fail_unescape(input, esc_pos, cur_pos + 1)

        # Join all characters into a string

        result: str = "".join(chr_lst)

        # Strip leading and/or trailing blanks if required, and return result

        return result.strip() if strip_blanks else result

    ###########################################################################

    @staticmethod
    def unquote(
        input: str | None,
        flags: EnvExpandFlags = EnvExpandFlags.DEFAULT,
        chars: EnvCharsData | None = None,
    ) -> tuple[str | None, EnvQuoteType]:
        """
        Remove enclosing quotes from a string ignoring everything beyond the
        closing quote ignoring escaped quotes. Raise ValueError if a dangling
        escape or no closing quote found.

        In most cases, you'd rather use Env.expand() that calls this method,
        then expands environment variables, arguments, and unescapes special
        characters.

        :param input: String to remove enclosing quotes from
        :type input: str | None

        :param flags: Flags controlling what/how to unquote input. Essentially,
            only two bits are considered: STRIP_SPACES and STRIP_COMMENT
        :type flags: EnvExpandFlags

        :param chars: Platform-specific special environment characters to
            parse various tokens like escaped characters, environment
            variables, etc.
        :type chars: EnvCharsData

        :return: Unquoted input and the type of surrounding quotes (see EnvQuoteType)
        :rtype: tuple[str | None, EnvQuoteType]
        """

        if chars is None:
            chars = EnvChars.Current

        if not input:
            return (input, EnvQuoteType.NONE)

        result, quote_type = Env.strip(input, flags=flags, chars=chars)

        if not result:
            return (result, quote_type)

        escape = chars.escape

        if quote_type == EnvQuoteType.HARD:
            quote = chars.hard_quote
            result = result[len(quote) :]
            end_pos = -1
            i = 0
            orig_len: int = len(result)
            while i < orig_len:
                if result[i] == escape and i + 1 < orig_len:
                    i += 2
                    continue
                if result[i] == quote:
                    end_pos = i
                    break
                i += 1
            if end_pos < 0:
                raise ValueError(f"Unterminated hard-quoted string: {input}")
            return (result[0:end_pos], EnvQuoteType.HARD)

        if quote_type == EnvQuoteType.NORMAL:
            quote = chars.normal_quote
            result = result[len(quote) :]
            end_pos = -1
            i = 0
            orig_len: int = len(result)
            while i < orig_len:
                if result[i] == escape and i + 1 < orig_len:
                    i += 2
                    continue
                if result[i] == quote:
                    end_pos = i
                    break
                i += 1
            if end_pos < 0:
                raise ValueError(f"Unterminated quoted string: {input}")
            return (result[0:end_pos], EnvQuoteType.NORMAL)

        cutter = chars.cutter

        if cutter:
            i = 0
            orig_len = len(result)
            cutter_len = len(cutter)
            strip_spaces = (flags & EnvExpandFlags.STRIP_SPACES) != 0
            while i < orig_len:
                if result[i] == escape and i + 1 < orig_len:
                    i += 2
                    continue
                if cutter_len == 1:
                    if result[i] == cutter:
                        result = result[0:i]
                        if strip_spaces:
                            result = result.rstrip()
                        break
                else:
                    if (
                        i + cutter_len <= orig_len
                        and result[i : i + cutter_len] == cutter
                    ):
                        result = result[0:i]
                        if strip_spaces:
                            result = result.rstrip()
                        break
                i += 1

        return (result, EnvQuoteType.NONE)

    ###########################################################################

    @staticmethod
    def __fail_unescape(input: str, beg_pos: int, end_pos: int):
        """
        Error handler for Env.unescape()

        :param input: Full string at fault
        :type input: str

        :param beg_pos: First index of the faulty fragment
        :type beg_pos: int

        :param end_pos: Last index of the faulty fragment
        :type end_pos: int

        :return: No return, exception raised
        :rtype: None
        """

        dtl = input[beg_pos:end_pos]

        raise ValueError(
            f'Incomplete escape sequence from [{beg_pos}]: "{dtl}" in "{input}"'
        )


###############################################################################
