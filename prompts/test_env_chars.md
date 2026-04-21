Execute prompts in test_env_chars.py and ensure that:

## TestEnvCharsConstants
- POSIX has expand="$", windup="", escape="\\", cutter="#", hard_quote="'", normal_quote='"'
- WINDOWS has expand="%", windup="%", escape="^", cutter="::", hard_quote="", normal_quote='"'
- RISCOS has expand="<", windup=">", escape="\\", cutter="|", hard_quote="", normal_quote='"'
- VMS has expand="'", windup="'", escape="^", cutter="!", hard_quote="", normal_quote='"'

## TestEnvCharsSelect
- select sets DEFAULT based on platform (IS_POSIX, IS_RISCOS, IS_VMS, IS_WINDOWS)
- select with "# test" sets CURRENT to POSIX (expand="$")
- select with "|test" sets CURRENT to RISCOS (expand="<")
- select with "!test" sets CURRENT to VMS (expand="'")
- select with "::test" sets CURRENT to WINDOWS (expand="%")
- select with empty string sets CURRENT to DEFAULT
- select copies constants (DEFAULT and CURRENT are not the same object as the ClassVars)

## TestEnvCharsMethods
- EnvChars.__init__ sets CURRENT and DEFAULT
- init with existing default skips init (DEFAULT is not None after first init)
- select returns EnvCharsData

## TestEnvCharsDataAttrs
- POSIX expand is "$"
- RISCOS expand is "<"
- WINDOWS expand is "%"