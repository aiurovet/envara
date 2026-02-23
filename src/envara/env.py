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
import re
import string
import sys
import fnmatch
import subprocess
import shlex
from typing import ClassVar

from env_exp_flags import EnvExpFlags
from env_platform_stack_flags import EnvPlatformStackFlags
from env_quote_type import EnvQuoteType
from env_parse_info import EnvParseInfo

###############################################################################


class Env:
    """
    Class for string expansions
    """

    # Default escape character
    POSIX_ESCAPE: ClassVar[str] = "\\"

    # Default expand character
    POSIX_EXPAND: ClassVar[str] = "$"

    # True if the app is running under Linux, UNIX, BSD, macOS or smimilar
    IS_POSIX: ClassVar[bool] = os.sep == "/"

    # True if the app is running under Risc OS
    IS_RISCOS: ClassVar[bool] = os.sep == "."

    # True if the app is running under OpenVMS or similar
    IS_VMS: ClassVar[bool] = os.sep == ":"

    # True if the app is running under Windows or OS/2
    IS_WINDOWS: ClassVar[bool] = os.sep == "\\"

    # A text indicating a POSIX-compatible platform
    PLATFORM_POSIX: ClassVar[str] = "posix"

    # A text indicating a Windows-compatible platform
    PLATFORM_WINDOWS: ClassVar[str] = "windows"

    # A text indicating the running platform
    PLATFORM_THIS: ClassVar[str] = sys.platform.lower()

    # Special characters when they follow an odd number of ESCAPEs
    SPECIAL: ClassVar[dict[str, str]] = {
        "a": "\a", "b": "\b", "f": "\f", "n": "\n",
        "r": "\r", "t": "\t", "v": "\v"
    }

    # Internal dictionary: regex => list-of-platform-names
    __platform_map: ClassVar[dict[str, list[str]]] = {
        "": ["", PLATFORM_POSIX], # the latter is checked
        "^aix": ["aix"],
        "android": ["linux", "android"],
        "^atheos": ["atheos"],
        "^beos|haiku": ["beos", "haiku"],
        "bsd": ["bsd"],
        "cygwin": ["cygwin"],
        "hp-ux": ["hp-ux"],
        "darwin|macos": ["bsd", "darwin", "macos"],
        "^ios|ipados": ["bsd", "ios"],
        "java": [PLATFORM_POSIX, PLATFORM_WINDOWS],  # only one will fit
        "^linux": ["linux"],
        "^os2": ["os2"],
        "^msys": ["msys"],
        "^riscos": ["riscos"],
        "sunos": ["sunos"],
        "unix": ["unix"],
        "vms": ["vms"],
        "^win": [PLATFORM_WINDOWS],
        ".+": [PLATFORM_THIS],
    }

    ###########################################################################

    @staticmethod
    def expand(
        input: str,
        args: list[str] | None = None,
        flags: EnvExpFlags | None = None,
        strip_spaces: bool = True,
        escapes: str = None,
        expands: str = None,
        hard_quotes: str = None,
        cutters: str = None,
    ) -> tuple[str, EnvParseInfo]:
        """
        Unquote the input if required, remove trailing line comment if
        required, expand the result with the arguments if required, expand
        the result with the environment variables' values. The method follows
        minimal POSIX conventions: $ABC and ${ABC}, as well as %ABC% on Windows

        :param input: Input string to expand
        :type input: str
        :param args: List of arguments to expand from $1, ...
        :type args: str
        :param flags: Flags controlling what/how to expand input
        :type flags: EnvExpandFlags
        :return: Expanded string
        :rtype: str
        """

        # If flags provided, map them to unquote parameters and post-processing

        if flags is None:
            flags = 0

        # Map flags to cutters/hard_quotes/unescape behaviours

        if (flags & EnvExpFlags.REMOVE_LINE_COMMENT) and (cutters is None):
            cutters = "#"

        info: EnvParseInfo

        _, info = Env.unquote(
            input,
            strip_spaces=strip_spaces,
            esc_chrs=escapes,
            exp_chrs=expands,
            cutters=cutters,
            hard_quotes=hard_quotes,
        )

        # SKIP_SINGLE_QUOTED prevents any expansion

        if (flags & EnvExpFlags.SKIP_SINGLE_QUOTED) and (info.quote_type.name == "SINGLE"):
            return (info.result, info)

        # SKIP_ENVIRON forcefully disables env var expansion.

        vars_dict = {} if (flags & EnvExpFlags.SKIP_ENV_VARS) else os.environ

        # Perform POSIX-style or Windows-style expansions based on
        # the first active expand character detected during unquoting

        if info.exp_chr == EnvParseInfo.POSIX_EXP_CHR:
            info.result = Env.expand_posix(
                info.result, args=args, vars=vars_dict,
                exp_chr=info.exp_chr, esc_chr=info.esc_chr
            )
        else:
            info.result = Env.expand_simple(
                info.result, args=args, vars=vars_dict,
                exp_chr=info.exp_chr, esc_chr=info.esc_chr
            )

        # Perform unescape if requested

        if (flags & EnvExpFlags.UNESCAPE):
            info.result = Env.unescape(info.result, escape=info.esc_chr)

        # Return the final result

        return (info.result, info)

    ###########################################################################

    @staticmethod
    def expand_posix(
        input: str,
        args: list[str] | None = None,
        vars: dict[str, str] | None = os.environ,
        exp_chr: str = "$",
        esc_chr: str = "\\",
        exp_flags: EnvExpFlags = EnvExpFlags.DEFAULT,
        subprocess_timeout: float | None = None,
    ) -> str:
        if input is None:
            return ""

        if vars is None:
            vars = os.environ

        allow_shell: bool =\
            (exp_flags & EnvExpFlags.ALLOW_SHELL) != 0

        allow_subprocess: bool =\
            allow_shell or\
            ((exp_flags & EnvExpFlags.ALLOW_SUBPROC) != 0)

        s = input
        res: list[str] = []
        i = 0
        inp_len = len(s)
        bktick = "`"
        is_bktick_cmd = bktick != esc_chr

        def get_var(name: str):
            return vars.get(name) if vars is not None else os.environ.get(name)

        def eval_braced(inner: str) -> str:
            # Length: #{NAME}
            if inner.startswith("#"):
                name = inner[1:]
                val = get_var(name)
                if val is None:
                    return f"{exp_chr}{{{inner}}}"
                return str(len(val))

            # Parse name
            m = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)', inner)
            if not m:
                # Support numeric positional parameters inside braces: ${1}, ${2}
                md = re.match(r'^(\d+)$', inner)
                if md:
                    idx = int(md.group(1)) - 1
                    if args and 0 <= idx < len(args):
                        return args[idx]
                    return f"{exp_chr}{{{inner}}}"
                return f"{exp_chr}{{{inner}}}"
            name = m.group(1)
            rest = inner[m.end():]

            val = get_var(name)
            is_set = val is not None
            is_null = (val == "") if is_set else False

            # Substring: :offset[:length]
            sm = re.match(r'^:(-?\d+)(?::(-?\d+))?$', rest)
            if sm:
                offset = int(sm.group(1))
                length = int(sm.group(2)) if sm.group(2) is not None else None
                if not is_set:
                    return f"{exp_chr}{{{inner}}}"
                text = val
                if offset < 0:
                    offset = len(text) + offset
                    if offset < 0:
                        offset = 0
                if length is None:
                    return text[offset:]
                return text[offset:offset + length]

            # Parameter expansion operators
            if rest.startswith(":=") or rest.startswith("="):
                assign_colon = rest.startswith(":=")
                word = rest[2:] if assign_colon else rest[1:]
                if (not is_set) or (assign_colon and is_null):
                    new_val = Env.expand_posix(word, args=args, vars=vars, exp_flags=exp_flags, subprocess_timeout=subprocess_timeout)
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
                    return f"{exp_chr}{{{inner}}}"
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
                    return f"{exp_chr}{{{inner}}}"
                text = val
                best_i = None
                for i in range(0, len(text) + 1):
                    sub = text[len(text) - i:]
                    if fnmatch.fnmatchcase(sub, pattern):
                        if rest.startswith("%%"):
                            best_i = i
                        else:
                            best_i = i
                            break
                if best_i is None:
                    return text
                return text[:len(text) - best_i]

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
                    return f"{exp_chr}{{{inner}}}"

                core = fnmatch.translate(pat)
                if core.startswith("(?s:") and core.endswith(")\\Z"):
                    core = core[4:-3]

                repl_eval = Env.expand_posix(repl, args=args, vars=vars, exp_flags=exp_flags, subprocess_timeout=subprocess_timeout)

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
                                sub = text[len(text) - i:]
                                if fnmatch.fnmatchcase(sub, pat):
                                    new_text = text[:len(text) - i] + repl_eval
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
                            sub = text[len(text) - i:]
                            if fnmatch.fnmatchcase(sub, pat):
                                return text[:len(text) - i] + repl_eval
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
                    return Env.expand_posix(word, args=args, vars=vars, exp_flags=exp_flags, subprocess_timeout=subprocess_timeout)
                return val
            if rest.startswith("-"):
                word = rest[1:]
                if not is_set:
                    return Env.expand_posix(word, args=args, vars=vars, exp_flags=exp_flags, subprocess_timeout=subprocess_timeout)
                return val
            if rest.startswith(":+"):
                word = rest[2:]
                if is_set and not is_null:
                    return Env.expand_posix(word, args=args, vars=vars, exp_flags=exp_flags, subprocess_timeout=subprocess_timeout)
                return ""
            if rest.startswith("+"):
                word = rest[1:]
                if is_set:
                    return Env.expand_posix(word, args=args, vars=vars, exp_flags=exp_flags, subprocess_timeout=subprocess_timeout)
                return ""
            if rest.startswith(":?"):
                word = rest[2:]
                if (not is_set) or is_null:
                    raise ValueError(Env.expand_posix(word, args=args, vars=vars, exp_flags=exp_flags, subprocess_timeout=subprocess_timeout) or f"{name}: parameter null or not set")
                return val
            if rest.startswith("?"):
                word = rest[1:]
                if not is_set:
                    raise ValueError(Env.expand_posix(word, args=args, vars=vars, subprocess_timeout=subprocess_timeout) or f"{name}: parameter not set")
                return val

            if is_set:
                return val
            return f"{exp_chr}{{{inner}}}"

        while i < inp_len:
            ch = s[i]

            if ch == esc_chr:
                j = i
                while j < inp_len and s[j] == esc_chr:
                    j += 1
                escape_count = j - i
                if (j < inp_len) and ((s[j] == exp_chr) or (is_bktick_cmd and (s[j] == bktick))):
                    res.append(esc_chr * (escape_count // 2))
                    if (escape_count % 2) == 1:
                        res.append(s[j])
                        i = j + 1
                        continue
                    i = j
                    continue
                else:
                    res.append(esc_chr * escape_count)
                    i = j
                    continue

            if is_bktick_cmd and (ch == bktick):
                j = i + 1
                while j < inp_len:
                    if s[j] == bktick:
                        break
                    if s[j] == esc_chr and (j + 1) < inp_len and s[j + 1] == bktick:
                        j += 2
                        continue
                    j += 1
                if j >= inp_len:
                    raise ValueError(f"Unterminated backtick command substitution in: {input}")
                inner = s[i + 1:j]
                cmd = Env.expand_posix(inner, args=args, vars=vars, exp_flags=exp_flags, subprocess_timeout=subprocess_timeout)
                if not allow_subprocess:
                    res.append(s[i:j + 1])
                    i = j + 1
                    continue
                try:
                    if allow_shell:
                        proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=subprocess_timeout)
                    else:
                        proc = subprocess.run(shlex.split(cmd), shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=subprocess_timeout)
                except subprocess.TimeoutExpired:
                    raise ValueError(f"Command substitution timed out: {cmd}")
                if proc.returncode != 0:
                    raise ValueError(f"Command substitution failed: {cmd}: {proc.stderr.strip()}")
                out = proc.stdout.rstrip('\n')
                res.append(out)
                i = j + 1
                continue

            if ch != exp_chr:
                res.append(ch)
                i += 1
                continue

            if (i + 1) < inp_len and s[i + 1] == exp_chr:
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
                inner = s[i + 2:j]
                cmd = Env.expand_posix(inner, args=args, vars=vars, exp_flags=exp_flags, subprocess_timeout=subprocess_timeout)
                if not allow_subprocess:
                    res.append(s[i:j + 1])
                    i = j + 1
                    continue
                try:
                    if allow_shell:
                        proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=subprocess_timeout)
                    else:
                        proc = subprocess.run(shlex.split(cmd), shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=subprocess_timeout)
                except subprocess.TimeoutExpired:
                    raise ValueError(f"Command substitution timed out: {cmd}")
                if proc.returncode != 0:
                    raise ValueError(f"Command substitution failed: {cmd}: {proc.stderr.strip()}")
                out = proc.stdout.rstrip('\n')
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
                inner = s[i + 2:j]
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

            res.append(exp_chr)
            i += 1

        return "".join(res)

    ###########################################################################

    @staticmethod
    def expand_simple(
        input: str,
        args: list[str] | None = None,
        vars: dict[str, str] | None = None,
        exp_chr: str = "%",
        esc_chr: str = "^",
    ) -> str:
        if input is None:
            return ""

        if vars is None:
            vars = os.environ

        s = input
        i = 0
        ln = len(s)
        out: list[str] = []

        while i < ln:
            ch = s[i]

            if ch == esc_chr:
                if (i + 1) < ln:
                    nxt = s[i + 1]
                    if nxt == exp_chr:
                        if (i + 2) < ln and s[i + 2] == exp_chr:
                            out.append(exp_chr)
                            i += 3
                            continue
                        if (i + 2) < ln and s[i + 2].isdigit():
                            j = i + 2
                            while j < ln and s[j].isdigit():
                                j += 1
                            out.append(exp_chr + s[i + 2:j])
                            i = j
                            continue
                        k = s.find(exp_chr, i + 2)
                        if k != -1:
                            out.append(s[i + 1:k + 1])
                            i = k + 1
                            continue
                        out.append(exp_chr)
                        i += 2
                        continue
                    out.append(nxt)
                    i += 2
                    continue
                else:
                    out.append(esc_chr)
                    i += 1
                    continue

            if ch != exp_chr:
                out.append(ch)
                i += 1
                continue

            if (i + 1) < ln and s[i + 1] == exp_chr:
                out.append(exp_chr)
                i += 2
                continue

            j = i + 1
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
                    end_with_exp_chr = False
                    if k < ln and s[k] == exp_chr:
                        end_with_exp_chr = True
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
                        if end_with_exp_chr:
                            out.append(exp_chr + s[j:k] + exp_chr)
                        else:
                            out.append(exp_chr + s[j:k])
                    i = k
                    continue

            if j < ln and s[j].isdigit():
                start = j
                while j < ln and s[j].isdigit():
                    j += 1
                end_with_exp_chr = False
                if j < ln and s[j] == exp_chr:
                    end_with_exp_chr = True
                    token = s[start:j]
                    j += 1
                else:
                    token = s[start:j]

                idx = int(token) - 1
                if args and 0 <= idx < len(args):
                    out.append(args[idx])
                else:
                    if end_with_exp_chr:
                        out.append(exp_chr + token + exp_chr)
                    else:
                        out.append(exp_chr + token)
                i = j
                continue

            if j < ln and s[j] == "*":
                j += 1
                if j < ln and s[j] == exp_chr:
                    j += 1
                if args:
                    out.append(" ".join(args))
                else:
                    out.append(exp_chr + "*")
                i = j
                continue

            k = s.find(exp_chr, j)
            if k == -1:
                out.append(exp_chr)
                i += 1
                continue

            token = s[j:k]
            if not token:
                out.append(exp_chr)
                out.append(exp_chr)
                i = k + 1
                continue

            if ":~" in token:
                base, suff = token.split(":~", 1)
                if not base:
                    out.append(exp_chr + token + exp_chr)
                    i = k + 1
                    continue
                if "," in suff:
                    start_str, length_str = suff.split(",", 1)
                else:
                    start_str = suff
                    length_str = None
                try:
                    start = int(start_str)
                    length = int(length_str) if (length_str is not None and length_str != "") else None
                except Exception:
                    out.append(exp_chr + token + exp_chr)
                    i = k + 1
                    continue

                val = vars.get(base)
                if val is None:
                    out.append(exp_chr + token + exp_chr)
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
                        substr = text[start:start + length]
                out.append(substr)
                i = k + 1
                continue

            name = token
            val = vars.get(name)
            if val is None:
                out.append(exp_chr + name + exp_chr)
            else:
                out.append(val)

            i = k + 1

        return "".join(out)

    ###########################################################################

    @staticmethod
    def get_all_platforms(
        flags: EnvPlatformStackFlags = EnvPlatformStackFlags.DEFAULT
    ) -> list[str]:
        """
        Get all supported platforms

        :param flags: Controls which items will be added to the stack
        :type flags: EnvPlatformStackFlags
        :param prefix: optional string to prepend to every platform name
        :type prefix: str | None
        :param suffix: optional string to append to every platform name
        :type suffix: str | None
        :return: A list of all relevant platforms (optionally decorated)
        :rtype: list[str]
        """

        # Initialize the return value

        result: list[str] = []

        # Add default platform if needed

        if flags & EnvPlatformStackFlags.ADD_EMPTY:
            result.append("")

        # Traverse the lists of platforms and append distinct

        for platforms in Env.__platform_map.values():
            for platform in platforms:
                if platform not in result:
                    result.append(platform)

        # Return the accumulated list

        return result

    ###########################################################################

    @staticmethod
    def get_cur_platforms(
        flags: EnvPlatformStackFlags = EnvPlatformStackFlags.DEFAULT,
        prefix: str | None = None,
        suffix: str | None = None,
    ) -> list[str]:
        """
        Get the stack (list) of platforms from more generic to more specific
        ones. Optionally add a prefix and/or suffix to every platform name
        (used by EnvFile to form filenames like '.env' or '.linux.env').

        :param flags: Controls which items will be added to the stack
        :type flags: EnvPlatformStackFlags
        :param prefix: optional string to prepend to every platform name
        :type prefix: str | None
        :param suffix: optional string to append to every platform name
        :type suffix: str | None
        :return: A list of all relevant platforms (optionally decorated)
        :rtype: list[str]
        """

        # Initialize the return value

        result: list[str] = []

        # Traverse the {pattern: list-of-relevant-platforms} dictionary and
        # append those where the pattern matches the running platform

        re_flags = re.IGNORECASE | re.UNICODE

        for pattern, platforms in Env.__platform_map.items():

            # If the platform doesn't match the running one, skip it

            if pattern:
                if not re.search(pattern, Env.PLATFORM_THIS, re_flags):
                    continue

            # Append every platform from the current list if eligible

            for platform in platforms:

                # Perform extra checks

                if not platform:
                    if (flags & EnvPlatformStackFlags.ADD_EMPTY) == 0:
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

        # Optionally decorate with prefix/suffix
        if prefix or suffix:
            decorated: list[str] = []
            for p in result:
                decorated.append(f"{prefix or ''}{p}{suffix or ''}")
            return decorated

        # Return the accumulated list

        return result

    ###########################################################################

    @staticmethod
    def quote(
        input: str,
        type: EnvQuoteType = EnvQuoteType.DOUBLE,
        escape: str = None
    ) -> str:
        """
        Enclose input in quotes. Neither leading, nor trailing whitespaces
        removed before checking the leading quotes. Use .strip() yourself
        before calling this method if needed.

        :param input: String being expanded
        :type input: str
        :param type: Type of quotes to enclose in
        :type type: EnvQuoteType
        :param escape: Escape character to use
        :type escape: str
        :return: Quoted string with possible quotes and escape characters from
                 the inside being escaped
        :rtype: str
        """

        # Initialise

        result = "" if (input is None) else input

        if (not escape):
            escape = EnvParseInfo.POSIX_ESC_CHR

        # Define the quote being used

        if type == EnvQuoteType.SINGLE:
            quote = "'"
        elif type == EnvQuoteType.DOUBLE:
            quote = '"'
        else:
            quote = ""

        # If quote is empty, return the input itself

        if not quote:
            return result

        # If input is not empty, escape the escape character, then the
        # internal quote(s), then embrace the result in desired quotes
        # and return

        if result and (quote in result):
            if escape in result:
                result = result.replace(escape, f"{escape}{escape}")
            result = result.replace(quote, f"{escape}{quote}")

        return f"{quote}{result}{quote}"

    ###########################################################################

    @staticmethod
    def unescape(
        input: str,
        escape: str = None,
        strip_blanks: bool = False,
    ) -> str:
        """
        Unescape '\\t', '\\n', '\\u0022' etc.

        :param input: Input string to unescape escaped characters in
        :type input: str
        :param escape: String to be treated as escape character
        :type expand_info: str
        :param strip_blanks: True = remove leading and trailing blanks
        :type strip_blanks: bool
        :return: Unescaped string, optionally, stripped of blanks
        :rtype: str
        """

        # If input is void, return empty string

        if not input:
            return ""

        # If escape character is not known yet, use the default one, and
        # if input does not contain the default escape char, then finish

        if (not escape):
            escape = EnvParseInfo.POSIX_ESC_CHR
            if escape not in input:
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

        for cur_chr in input:
            cur_pos = cur_pos + 1

            if (cur_pos >= acc_beg_pos) and (cur_pos < acc_end_pos):
                if (cur_chr not in string.hexdigits):
                    Env.__fail_unescape(input, esc_pos, cur_pos)
                continue

            if (cur_pos == acc_end_pos):
                chr_lst.append(chr(int(input[acc_beg_pos:acc_end_pos], 16)))
                is_escaped = False

            if (cur_chr == escape):
                is_escaped = not is_escaped
                esc_pos = cur_pos if (is_escaped) else -1
                continue

            if (is_escaped):
                if (cur_chr in Env.SPECIAL):
                    cur_chr = Env.SPECIAL[cur_chr]
                elif (cur_chr == "u"):
                    acc_beg_pos = cur_pos + 1
                    acc_end_pos = acc_beg_pos + 4
                    continue
                elif (cur_chr == "x"):
                    acc_beg_pos = cur_pos + 1
                    acc_end_pos = acc_beg_pos + 2
                    continue
                is_escaped = False

            chr_lst.append(cur_chr)

        # If escaped char (by code) is the last one, accumulation
        # action was missed from the loop: fulfilling here

        if is_escaped:
            if (acc_end_pos > 0):
                if (cur_pos >= acc_end_pos - 1):
                    chr_lst.append(chr(int(input[acc_beg_pos:acc_end_pos], 16)))
                elif (esc_pos >= 0):
                    Env.__fail_unescape(input, esc_pos, cur_pos + 1)
            elif (esc_pos >= 0):
                Env.__fail_unescape(input, esc_pos, cur_pos + 1)

        # Join all characters into a string

        result: str = "".join(chr_lst)

        # Get the indicator of loeading or trailing blanks Turn off stripping leading and trailing blanks if not found

        res_len = len(result) if strip_blanks else 0

        has_blanks: bool = \
            (res_len > 0) and \
            (result[0] in string.whitespace) and \
            (result[res_len - 1] in string.whitespace)

        return result.strip() if (has_blanks) else result

    ###########################################################################

    @staticmethod
    def unquote(
        input: str,
        strip_spaces: bool = True,
        esc_chrs: str = None,
        exp_chrs: str = None,
        hard_quotes: str = None,
        cutters: str = None,
    ) -> tuple[str, EnvParseInfo]:
        """
        Remove enclosing quotes from a string ignoring everything beyond the
        closing quote ignoring escaped quotes. Raise ValueError if a dangling
        escape or no closing quote found.
        
        In most cases, you'd rather use _Env.unquote()_ that calls this method,
        then expands environment variables, arguments, and unescapes special
        characters.
        
        :param input: String to remove enclosing quotes from
        :type input: str
        :param escape: Escape characters: whichever comes first in the input
                       will be returned in the dedicated info
        :type escapes: str
        :param strip_spaces: True = strip leading and trailing spaces. If
                             quoted, don't strip again after unquoting
        :type strip_spaces: bool
        :param expands: A string of characters where each indicates a start
                        of env var or arg expansion (e.g., "$%")
        :type expands: str
        :param hard_quotes: A string containing all quote characters that
                            require to ignore escaping (e.g., a single quote)
        :type hard_quotes: bool
        :param cutters: A string of characters where each indicates a string
                         end when found non-escaped and either outside quotes
                         or in an unquoted input (e.g., a line comment: "#")
        :type cutters: str
        :return: unquoted input and details: see _EnvUnquoteData_
        :rtype: tuple[str, EnvUnquoteData]
        """

        # Initialize

        info = EnvParseInfo(input=input, quote_type=EnvQuoteType.NONE)

        # If the input is None or empty, return the empty string

        if (not input):
            return (info.result, info)

        # Ensure required arguments are populated

        if (exp_chrs is None):
            exp_chrs = EnvParseInfo.POSIX_EXP_CHR
        if (esc_chrs is None):
            esc_chrs = EnvParseInfo.POSIX_ESC_CHR

        # Initialize position beyond the last character and results

        end_pos: int = 0
        info.result = input.lstrip() if (strip_spaces) else input

        if (not info.result):
            return (info.result, info)

        # Initialise quote and determine quote type

        info.quote = info.result[0]

        if (info.quote == '"'):
            info.quote_type = EnvQuoteType.DOUBLE
        elif (info.quote == "'"):
            info.quote_type = EnvQuoteType.SINGLE
        else:
            info.quote = ""

        # Initialise flags for escaping and quoting

        has_cutters: bool = True if cutters else False
        is_escaped: bool = False
        is_quoted: bool = info.quote_type != EnvQuoteType.NONE

        # Avoid Nones

        if (hard_quotes is None):
            hard_quotes = "'"

        # No escape is relevant if the given quote is the hard one

        if is_quoted and (info.quote in hard_quotes):
            esc_chrs = ""

        # Loop through each input character and analyze

        for cur_chr in info.result:
            # Advance the end position and skip opening quote if present

            end_pos = end_pos + 1

            if (end_pos == 1) and is_quoted:
                continue

            # If an escape encountered, flip the flag and loop

            if (cur_chr in esc_chrs):
                info.esc_chr = cur_chr
                is_escaped = not is_escaped
                continue

            # When a quote is encountered, if escaped, loop, else,
            # this quote is the closing one, so return the result.

            if (cur_chr == info.quote):
                if is_quoted and (info.quote in hard_quotes):
                    is_quoted = False
                    break
                if (is_escaped):
                    is_escaped = False
                    continue
                if (is_quoted):
                    is_quoted = False
                    break
                else:
                    continue

            # Set expand character if found first time

            if (cur_chr in exp_chrs):
                if (not info.exp_chr) and (not is_escaped):
                    info.exp_chr = cur_chr

            # Break out if the stopper character was encountered outside
            # the quotes, and it was not escaped

            if (not is_quoted) and (not is_escaped):
                if has_cutters and (cur_chr in cutters):
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

        if info.quote_type == EnvQuoteType.NONE:
            beg_pos = 0
        else:
            beg_pos = 1
            end_pos = end_pos - 1

        # Extract the unquoted substring

        info.result = info.result[beg_pos:end_pos]

        # Strip trailing spaces if needed, but only if the original input
        # was not quoted

        if strip_spaces and (info.quote_type == EnvQuoteType.NONE):
            info.result = info.result.rstrip()

        # Return the result

        return (info.result, info)

    ###########################################################################

    @staticmethod
    def __fail_unescape(input: str, beg_pos: int, end_pos: int):
        """
        Error handler for Env.unescape()
        
        :param input: Full string at fault
        :type input: str
        :param beg_pos: Starting position of the fragment at fault
        :type beg_pos: int
        :param end_pos: Ending position of the fragment at fault
        :type end_pos: int
        :return: Raise exception
        :rtype: None
        """

        dtl: str = input[beg_pos:end_pos]

        raise ValueError(
            f"Incomplete escape sequence from [{beg_pos}]: \"{dtl}\" in \"{input}\""
        )


###############################################################################
