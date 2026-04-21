from pathlib import Path
import sys
import os

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "envara"))

import envara
import env_chars
import env_chars_data
import env_filter
import env_filters
import env_file
import env_file_flags
import env_expand_flags

envara.Env = type("Env", (), {})()
envara.EnvChars = env_chars.EnvChars
envara.EnvCharsData = env_chars_data.EnvCharsData

env_chars_mod = env_chars
env_chars_data_mod = env_chars_data
env_filter_mod = env_filter
env_filters_mod = env_filters
env_file_mod = env_file
env_file_flags_mod = env_file_flags
env_expand_flags_mod = env_expand_flags
envara_mod = envara

os.chdir(str(Path(__file__).parent.parent))