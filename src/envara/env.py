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
from typing import ClassVar

from envara.env_expand_flags import EnvExpandFlags
from envara.env_platform_flags import EnvPlatformFlags
from envara.env_quote_type import EnvQuoteType
from env_chars import EnvChars

###############################################################################


class Env:
    """
    Class for string expansions
    """

    CMD_SPLIT_RE: ClassVar[re.Pattern] = re.compile("'([^']*)'|\"([^\"]*)\"|([^\s]+)")
    """Regular expression to split command into array after escaped characters were hidden"""

    IS_POSIX: ClassVar[bool] = os.sep == "/"
    """True if the app is running under Linux, UNIX, BSD, macOS or smimilar"""

    IS_RISCOS: ClassVar[bool] = os.sep == "."
    """True if the app is running under Risc OS"""

    IS_VMS: ClassVar[bool] = os.sep == ":"
    """True if the app is running under OpenVMS or similar"""

    IS_WINDOWS: ClassVar[bool] = os.sep == "\\"
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
        "^riscos": ["riscos"],
        "vms": ["vms"],
        ".+": [PLATFORM_THIS],
    }
    """Dictionary: regex => list-of-platform-names"""

    ###########################################################################

    @staticmethod
    def expand(
        input: Path | str,
        args: list[str] | None = None,
        flags: EnvExpandFlags = EnvExpandFlags.DEFAULT,
        chars: EnvChars = EnvChars.CURRENT
    ) -> Path | str:
        """
        Unquote the input if required via flags, remove trailing line comment
        if required via flags, expand the result with the arguments if
        required via flags, expand the result with the environment variables'
        values. The method follows POSIX and DOS/Windows expansion conventions
        depending on what was found first: dollar or percent, then backslash
        or caret (obviously, the POSIX style is by far more advanced)

        :param input: Path or string to expand
        :type input: Path  | str

        :param args: List of arguments to expand $#, $1, $2, ...
        :type args: str

        :param flags: Flags controlling what/how to expand input
        :type flags: EnvExpandFlags

        :param chars: Enviroment-specific characters to parse various tokens
            like escaped characters, environment variables, etc.
        :type chars: EnvChars

        :return: Expanded string or Path object
        :rtype: Path | str
        """

        # If flags provided, map them to unquote parameters and post-processing

        if flags is None:
            flags = EnvExpandFlags.DEFAULT

        # Check what should be the type of expanded input

        is_path: bool = isinstance(input, Path)

        # Remove quotes if found

        result, quote_type = Env.unquote(
            str(input) if is_path else input,
            flags=flags,
            chars=chars
        )

        # SKIP_SINGLE_QUOTED prevents any expansion

        if flags & EnvExpandFlags.SKIP_LITERAL:
            if quote_type == EnvQuoteType.HARD:
                return result

        # SKIP_ENVIRON forcefully disables env var expansion.

        vars_dict = {} if (flags & EnvExpandFlags.SKIP_ENV_VARS) else os.environ

        # Perform POSIX-style or Windows-style expansions based on
        # the first active expand character detected during unquoting

        if chars == EnvChars.POSIX:
            result = Env.expand_posix(
                result,
                args=args,
                vars=vars_dict,
                chars=chars
            )
        else:
            result = Env.expand_simple(
                result,
                args=args,
                vars=vars_dict,
                chars=chars,
            )

        # Perform unescape if requested

        if flags & EnvExpandFlags.UNESCAPE:
            result = Env.unescape(result, chars=chars)

        # Reeturn final result

        return Path(result) if is_path else result

    ###########################################################################
    # This code was mainly generated using Copilot
    ###########################################################################

    @staticmethod
    def expand_posix(
        input: Path | str,
        args: list[str] | None = None,
        vars: dict[str, str] | None = os.environ,
        chars: EnvChars = EnvChars.POSIX,
        expand_flags: EnvExpandFlags = EnvExpandFlags.DEFAULT,
        subprocess_timeout: float | None = None,
    ) -> Path | str:
        """
        Expand environment variables and sub-processes according to complex
        POSIX rules: like ${ABC:-${DEF:-$(uname -a)}. See the description
        of arguments under the main method expand(...)
        """
        if input is None:
            return ""

        is_path = isinstance(input, Path)

        if vars is None:
            vars = os.environ

        allow_shell: bool = (expand_flags & EnvExpandFlags.ALLOW_SHELL) != 0

        allow_subprocess: bool = allow_shell or (
            (expand_flags & EnvExpandFlags.ALLOW_SUBPROC) != 0
        )

        s = str(input) if is_path else input
        res: list[str] = []
        i = 0
        inp_len = len(s)
        bktick = "`"
        is_bktick_cmd = bktick != chars.escape

        expand_char = chars.expand
        escape_char = chars.escape

        def get_var(name: str):
            return vars.get(name) if vars is not None else os.environ.get(name)

        def eval_braced(inner: str) -> str:
            # Length: #{NAME}
            if inner.startswith("#"):
                name = inner[1:]
                val = get_var(name)
                if val is None:
                    return f"{expand_char}{{{inner}}}"
                return str(len(val))

            # Parse name
            m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)", inner)
            if not m:
                # Support numeric positional parameters inside braces: ${1}, ${2}
                md = re.match(r"^(\d+)$", inner)
                if md:
                    idx = int(md.group(1)) - 1
                    if args and 0 <= idx < len(args):
                        return args[idx]
                    return f"{expand_char}{{{inner}}}"
                return f"{expand_char}{{{inner}}}"
            name = m.group(1)
            rest = inner[m.end() :]

            val = get_var(name)
            is_set = val is not None
            is_null = (val == "") if is_set else False

            # Substring: :offset[:length]
            sm = re.match(r"^:(-?\d+)(?::(-?\d+))?$", rest)
            if sm:
                offset = int(sm.group(1))
                length = int(sm.group(2)) if sm.group(2) is not None else None
                if not is_set:
                    return f"{expand_char}{{{inner}}}"
                text = val
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
                    new_val = Env.expand_posix(
                        word,
                        args=args,
                        vars=vars,
                        expand_flags=expand_flags,
                        subprocess_timeout=subprocess_timeout,
                    )
                    try:
                        if vars is not None:
                            vars[name] = new_val
                    except Exception:
                        pass
                    return new_val
                return val

            # Pattern removals: #, ## (prefix) and %, %% (suffix)
            if rest.startswith("##") or rest.startswith("#"):
                pattern = rest[2:] if rest.startswith("##") else rest[1:]
                if not is_set:
                    return f"{expand_char}{{{inner}}}"
                text = val
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
                text = val
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
            if r and r[0] in ("#", "%"):
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
                if core.startswith("(?s:") and core.endswith(")\\Z"):
                    core = core[4:-3]

                repl_eval = Env.expand_posix(
                    repl,
                    args=args,
                    vars=vars,
                    expand_flags=expand_flags,
                    subprocess_timeout=subprocess_timeout,
                )

                if anchor == "#":
                    text = val
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
                        return val

                if anchor == "%":
                    text = val
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
                        return val

                pattern = core
                prog = re.compile(pattern, re.DOTALL)
                if is_all:
                    return prog.sub(repl_eval, val)
                else:
                    return prog.sub(repl_eval, val, count=1)

            if rest.startswith(":-"):
                word = rest[2:]
                if (not is_set) or is_null:
                    return Env.expand_posix(
                        word,
                        args=args,
                        vars=vars,
                        expand_flags=expand_flags,
                        subprocess_timeout=subprocess_timeout,
                    )
                return val
            if rest.startswith("-"):
                word = rest[1:]
                if not is_set:
                    return Env.expand_posix(
                        word,
                        args=args,
                        vars=vars,
                        expand_flags=expand_flags,
                        subprocess_timeout=subprocess_timeout,
                    )
                return val
            if rest.startswith(":+"):
                word = rest[2:]
                if is_set and not is_null:
                    return Env.expand_posix(
                        word,
                        args=args,
                        vars=vars,
                        expand_flags=expand_flags,
                        subprocess_timeout=subprocess_timeout,
                    )
                return ""
            if rest.startswith("+"):
                word = rest[1:]
                if is_set:
                    return Env.expand_posix(
                        word,
                        args=args,
                        vars=vars,
                        expand_flags=expand_flags,
                        subprocess_timeout=subprocess_timeout,
                    )
                return ""
            if rest.startswith(":?"):
                word = rest[2:]
                if (not is_set) or is_null:
                    raise ValueError(
                        Env.expand_posix(
                            word,
                            args=args,
                            vars=vars,
                            expand_flags=expand_flags,
                            subprocess_timeout=subprocess_timeout,
                        )
                        or f"{name}: parameter null or not set"
                    )
                return val
            if rest.startswith("?"):
                word = rest[1:]
                if not is_set:
                    raise ValueError(
                        Env.expand_posix(
                            word,
                            args=args,
                            vars=vars,
                            subprocess_timeout=subprocess_timeout,
                        )
                        or f"{name}: parameter not set"
                    )
                return val

            if is_set:
                return val
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
                cmd = Env.expand_posix(
                    inner,
                    args=args,
                    vars=vars,
                    expand_flags=expand_flags,
                    subprocess_timeout=subprocess_timeout,
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
                cmd = Env.expand_posix(
                    inner,
                    args=args,
                    vars=vars,
                    expand_flags=expand_flags,
                    subprocess_timeout=subprocess_timeout,
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
                    val = get_var(name)
                    if val is None:
                        res.append(s[i:j])
                    else:
                        res.append(val)
                    i = j
                    continue

            res.append(expand_char)
            i += 1

        result = "".join(res)

        return Path(result) if is_path else result

    ###########################################################################
    # This code was mainly generated using Copilot
    ###########################################################################

    @staticmethod
    def expand_simple(
        input: str,
        args: list[str] | None = None,
        vars: dict[str, str] | None = None,
        chars: EnvChars = EnvChars.CURRENT,
    ) -> str:
        """
        Expand environment variables and sub-processes according to simple
        rules and symmetric expand characters: like %ABC% in Windows. See
        the description of arguments under the main method expand(...)
        """
        if input is None:
            return ""

        is_path = isinstance(input, Path)

        if vars is None:
            vars = os.environ

        expand_char: str = chars.expand
        windup_char: str = chars.windup
        escape_char: str = chars.escape

        is_flexible = (
            expand_char != EnvChars.RISCOS_EXPAND
            and expand_char != EnvChars.VMS_EXPAND
        )

        windup = windup_char or expand_char

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
                        k = s.find(windup, i + 2)
                        if k != -1:
                            out.append(s[i + 1 : k + 1])
                            i = k + 1
                            continue
                        out.append(expand_char)
                        i += 2
                        continue
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

            if (i + 1) < ln and s[i + 1] == windup:
                out.append(expand_char)
                i += 2
                continue

            j = i + 1

            if is_flexible:
                if j < ln and s[j] == "~":
                    k = j + 1
                    mods = []
                    while k < ln and s[k].isalpha():
                        mods.append(s[k])
                        k += 1
                    if k < ln and s[k].isdigit():
                        start = k
                        while k < ln and s[k].isdigit():
                            k += 1
                        token = s[start:k]
                        end_with_windup = False
                        if k < ln and s[k] == windup:
                            end_with_windup = True
                            k += 1

                        idx = int(token) - 1
                        if args and 0 <= idx < len(args):
                            tokval = args[idx]

                            def part_drive(t):
                                return os.path.splitdrive(t)[0]

                            def part_path(t):
                                p = os.path.dirname(t)
                                if p and not p.endswith(os.sep):
                                    p = p + os.sep
                                return p

                            def part_name(t):
                                return os.path.splitext(os.path.basename(t))[0]

                            def part_ext(t):
                                return os.path.splitext(t)[1]

                            def part_full(t):
                                return os.path.abspath(t)

                            out_frag = []
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
                                out.append(expand_char + s[j:k] + windup)
                            else:
                                out.append(expand_char + s[j:k])
                        i = k
                        continue

                if j < ln and s[j].isdigit():
                    start = j
                    while j < ln and s[j].isdigit():
                        j += 1
                    end_with_windup = False
                    if j < ln and s[j] == windup:
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
                            out.append(expand_char + token + windup)
                        else:
                            out.append(expand_char + token)
                    i = j
                    continue

                if j < ln and s[j] == "*":
                    j += 1
                    if j < ln and s[j] == windup:
                        j += 1
                    if args:
                        out.append(" ".join(args))
                    else:
                        out.append(expand_char + "*")
                    i = j
                    continue

            k = s.find(windup, j)
            if k == -1:
                out.append(expand_char)
                i += 1
                continue

            token = s[j:k]
            if not token:
                out.append(expand_char)
                out.append(windup)
                i = k + 1
                continue

            if is_flexible and (":~" in token):
                base, suff = token.split(":~", 1)
                if not base:
                    out.append(expand_char + token + windup)
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
                    out.append(expand_char + token + windup)
                    i = k + 1
                    continue

                val = vars.get(base)
                if val is None:
                    out.append(expand_char + token + windup)
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
                out.append(expand_char + name + windup)
            else:
                out.append(val)

            i = k + 1

        result = "".join(out)

        return Path(result) if is_path else result

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

                # Perform extra checks

                if not platform:
                    continue
                elif platform == Env.PLATFORM_POSIX:
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
        type: EnvQuoteType = EnvQuoteType.DEFAULT,
        chars: EnvChars = EnvChars.CURRENT
    ) -> str:
        """
        Enclose input in quotes. Neither leading, nor trailing whitespaces
        removed before checking the leading quotes. Use .strip() yourself
        before calling this method if needed.

        :param input: String being expanded
        :type input: str

        :param type: Type of quotes to enclose in
        :type type: EnvQuoteType

        :param chars: Enviroment-specific characters to parse various tokens
            like escaped characters, environment variables, etc.
        :type chars: EnvChars

        :return: Quoted string with possible quotes and escape characters from
                 the inside being escaped
        :rtype: str
        """

        # Initialise

        result = "" if (input is None) else input
        escape_char = chars.escape

        # Define the quote being used

        if type == EnvQuoteType.HARD:
            quote = chars.hard_quote
        elif type == EnvQuoteType.NORMAL:
            quote = chars.normal_quote
        else:
            quote = ""

        # If quote is empty, return the input itself

        if not quote:
            return result

        # If input is not empty, escape the escape character, then the
        # internal quote(s), then embrace the result in desired quotes
        # and return

        if result and (quote in result):
            if escape_char in result:
                result = result.replace(escape_char, f"{escape_char}{escape_char}")
            result = result.replace(quote, f"{escape_char}{quote}")

        return f"{quote}{result}{quote}"

    ###########################################################################

    @staticmethod
    def split_command(
        input: str,
        args: list[str] | None = None,
        flags: EnvExpandFlags = EnvExpandFlags.DEFAULT,
        chars: EnvChars = EnvChars.CURRENT
   ) -> list[str]:
        """
        Treat the input string as command and split it into array of strings
        where the first item is executable, and the rest are the arguments
        (pipe and beyond are treated as arguments too). Then if flags not set
        to EnvExpandFlags.NONE, expand environment variables and application
        arguments in every token that is not a literal string

        :param input: Input string to split
        :type input: str

        :param args: List of arguments to expand $#, $1, $2, ...
        :type args: str

        :param flags: Flags controlling what/how to expand input
        :type flags: EnvExpandFlags

        :param chars: Enviroment-specific characters to parse various tokens
            like escaped characters, environment variables, etc.
        :type chars: EnvChars

        :return: List of strings representing the executable and its arguments
        :rtype: str
        """
        # Resolve escape character if not specified

        escape_char: str = chars.escape

        # Prepare special characters that should be temporarily hidden

        escape_char_escaped: str = escape_char + escape_char
        apos_char_escaped: str = escape_char + "'" if Env.IS_POSIX else None
        quote_char_escaped: str = escape_char + '"'
        space_char_escaped: str = escape_char + " "
        tab_char_escaped: str = escape_char + "\t"

        # Make a copy of the input string by resolving continued lines and
        # temporarily hiding special characters

        input_ex: str = input\
            .replace(escape_char + "\r\n", " ")\
            .replace(escape_char + "\n", " ")\
            .replace(escape_char_escaped, "\x01")\
            .replace(tab_char_escaped, "\x02")\
            .replace(space_char_escaped, "\x03")\
            .replace(quote_char_escaped, "\x04")

        if Env.IS_POSIX:
            input_ex = input_ex.replace(apos_char_escaped, "\x05")
 
        # Prepare result list and a pattern callback

        result: list[str] = []

        def sub_proc(m: re.Match):
            """
            A callback to process the command-line tokens (arguments)
            found in the input
            """
            grps = m.groups()
            token: str = grps[0]

            if token and Env.IS_POSIX:
                # If hard-quoted token of the original input, and in POSIX,
                # restore all hidden characters as they were

                result.append(
                    token.replace("\x05", apos_char_escaped)\
                        .replace("\x04", quote_char_escaped)\
                        .replace("\x03", space_char_escaped)\
                        .replace("\x02", tab_char_escaped)\
                        .replace("\x01", escape_char_escaped)\
                )
            else:
                # If a normally quoted or plain token, replace the previously
                # hidden characters with their unescaped equivalents

                if not token:
                    token = grps[1] or grps[2]

                if Env.IS_POSIX:
                    token = token.replace("\x05", "'")

                token = token\
                    .replace("\x04", '"')\
                    .replace("\x03", " ")\
                    .replace("\x02", "\t")\
                    .replace("\x01", escape_char)

                result.append(
                    Env.expand(token, args=args, flags=flags, chars=chars)
                )

            # Doesn't matter what to return, as that value won't be used

            return ""

        Env.CMD_SPLIT_RE.sub(sub_proc, input_ex)

        return result

    ###########################################################################

    @staticmethod
    def unescape(
        input: str,
        strip_blanks: bool = False,
        chars: EnvChars = EnvChars.CURRENT
    ) -> str:
        """
        Unescape '\\t', '\\n', '\\u0022' etc.

        :param input: Input string to unescape escaped characters in
        :type input: str

        :param strip_blanks: True = remove leading and trailing blanks
        :type strip_blanks: bool

        :param chars: Enviroment-specific characters to parse various tokens
            like escaped characters, environment variables, etc.
        :type chars: EnvChars

        :return: Unescaped string, optionally, stripped of blanks
        :rtype: str
        """

        # If input is void, return empty string

        if not input:
            return ""

        # If escape character is empty or if the input does not contain it,
        # then finish

        if (not chars.escape) or chars.escape not in input:
            return input

        # Loop through the input and accumulate valid characters in chr_lst

        chr_lst: list[str] = []
        cur_pos: int = -1
        esc_pos: int = -1
        is_escaped: bool = False

        # Start and end of a substring to accumulate for the code-to-string
        # conversion

        acc_beg_pos: int = -1
        acc_end_pos: int = -1

        for cur_char in input:
            cur_pos = cur_pos + 1

            if (cur_pos >= acc_beg_pos) and (cur_pos < acc_end_pos):
                if cur_char not in string.hexdigits:
                    Env.__fail_unescape(input, esc_pos, cur_pos)
                continue

            if cur_pos == acc_end_pos:
                chr_lst.append(chr(int(input[acc_beg_pos:acc_end_pos], 16)))
                is_escaped = False

            if cur_char in chars.escape:
                is_escaped = not is_escaped
                esc_pos = cur_pos if (is_escaped) else -1
                continue

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

            chr_lst.append(cur_char)

        # If escaped char (by code) is the last one, accumulation
        # action was missed from the loop: fulfilling here

        if is_escaped:
            if acc_end_pos > 0:
                if cur_pos >= acc_end_pos - 1:
                    chr_lst.append(chr(int(input[acc_beg_pos:acc_end_pos], 16)))
                elif esc_pos >= 0:
                    Env.__fail_unescape(input, esc_pos, cur_pos + 1)
            elif esc_pos >= 0:
                Env.__fail_unescape(input, esc_pos, cur_pos + 1)

        # Join all characters into a string

        result: str = "".join(chr_lst)

        # Strip leading and/or trailing blanks if required, and return result

        return result.strip() if strip_blanks else result

    ###########################################################################

    @staticmethod
    def unquote(
        input: str,
        flags: EnvExpandFlags = EnvExpandFlags.DEFAULT,
        chars: EnvChars = EnvChars.CURRENT
    ) -> tuple[str, EnvQuoteType]:
        """
        Remove enclosing quotes from a string ignoring everything beyond the
        closing quote ignoring escaped quotes. Raise ValueError if a dangling
        escape or no closing quote found.

        In most cases, you'd rather use _Env.unquote()_ that calls this method,
        then expands environment variables, arguments, and unescapes special
        characters.

        :param input: String to remove enclosing quotes from
        :type input: str

        :param flags: Flags controlling what/how to unquote input
        :type flags: EnvExpandFlags

        :param chars: Enviroment-specific characters to parse various tokens
            like escaped characters, environment variables, etc.
        :type chars: EnvChars

        :return: Unquoted input and the type of surrounding quotes (see EnvQuoteType)
        :rtype: tuple[str, EnvQuoteType]
        """

        # If the input is None or empty, return the empty string

        if not input:
            return (input, EnvQuoteType.NONE)

        # Initialize position beyond the last character and results

        strip_spaces: bool = True if flags & EnvExpandFlags.STRIP_SPACES else False
        cur_pos: int = 0
        end_pos: int = 0
        quote_type: EnvQuoteType = EnvQuoteType.NONE
        result: str = input.lstrip() if (strip_spaces) else input

        if not result:
            return (result, EnvQuoteType.NONE)

        # Initialise flags for escaping and quoting

        if (flags & EnvExpandFlags.REMOVE_LINE_COMMENT) and chars.cutter:
            has_cutter = True
        else:
            has_cutter = False

        is_cut: bool = False
        is_escaped: bool = False
        is_quoted: bool = False
        is_hard_quoted: bool = False

        # Loop through each input character and analyze

        for cur_char in result:
            # Advance the current and end position and skip opening quote if present

            cur_pos = end_pos
            end_pos = end_pos + 1

            if (end_pos == 1) and is_quoted:
                continue

            # If an escape encountered, flip the flag, set escape char and loop

            if cur_char in chars.escape:
                if (chars.escape_len <= 1) or result.startswith(chars.escape, start=cur_pos):
                    is_escaped = not is_escaped
                    continue

            # When a hard quote is encountered, and was quoted, this quote is
            # the closing one, so return the result. Otherwise, set the flags
            # and continue

            if cur_char in chars.hard_quote:
                if is_hard_quoted:
                    is_hard_quoted = False
                    is_quoted = False
                    break
                else:
                    quote_type = EnvQuoteType.HARD
                    is_hard_quoted = True
                    is_quoted = True
                    continue

            # When a normal quote is encountered, if escaped, loop, else,
            # this quote is the closing one, so return the result.

            if cur_char in chars.normal_quote:
                if is_escaped:
                    is_escaped = False
                    continue
                if is_hard_quoted:
                    continue
                if is_quoted:
                    break
                else:
                    quote_type = EnvQuoteType.NORMAL
                    is_quoted = True
                    continue

            # Break out if the cutter was encountered outside
            # the quotes, and it was not escaped

            if has_cutter and (cur_char in chars.cutter):
                if is_escaped:
                    is_escaped = False
                    continue
                if (not is_quoted) and (not is_escaped) and not is_cut:
                    if result.startswith(chars.cutter, cur_pos):
                        is_cut = True
                        end_pos = end_pos - 1
                        break

            # For any other character, discard is_escaped

            is_escaped = False

        # Check the malformed input

        if is_escaped:
            raise ValueError(f"A dangling escape found in: {input}")

        if is_quoted:
            raise ValueError(f"Unterminated quoted string: {input}")

        # Calculate the unquoted substring

        if quote_type == EnvQuoteType.NONE:
            cur_pos = 0
        else:
            cur_pos = 1
            end_pos = end_pos - 1

        # Extract the unquoted substring

        result = result[cur_pos:end_pos]

        # Strip trailing spaces if needed, but only if the original input
        # was not quoted

        if strip_spaces and (quote_type == EnvQuoteType.NONE):
            result = result.rstrip()

        # Return the result

        return (result, quote_type)

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

        dtl: str = input[beg_pos:end_pos]

        raise ValueError(
            f'Incomplete escape sequence from [{beg_pos}]: "{dtl}" in "{input}"'
        )


###############################################################################
