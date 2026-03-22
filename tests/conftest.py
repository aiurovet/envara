from pathlib import Path
import sys

project_dir = Path(__file__).parent.parent

sys.path.insert(0, str(project_dir / "src"))
sys.path.insert(0, str(project_dir / "src" / "envara"))
