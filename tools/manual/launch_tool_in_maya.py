import sys
import importlib
from pathlib import Path

REPO_ROOT = r"C:\Users\gusta\Documents\GitHub\Maya Production Pipeliner"

repo_path = Path(REPO_ROOT).resolve()

if not repo_path.exists():
    raise RuntimeError("REPO_ROOT does not exist: %s" % repo_path)

package_path = repo_path / "maya_production_pipeliner"

if not package_path.exists():
    raise RuntimeError(
        "maya_production_pipeliner package not found inside REPO_ROOT: %s" % package_path
    )

repo_root_str = str(repo_path)

if repo_root_str not in sys.path:
    sys.path.insert(0, repo_root_str)

MODULE_NAMES = (
    "maya_production_pipeliner.config",
    "maya_production_pipeliner.scanner",
    "maya_production_pipeliner.classifier",
    "maya_production_pipeliner.organizer",
    "maya_production_pipeliner.reporter",
    "maya_production_pipeliner.mel_bridge",
    "maya_production_pipeliner.pipeline",
    "maya_production_pipeliner.ui",
    "maya_production_pipeliner.launcher",
)

for module_name in MODULE_NAMES:
    module = sys.modules.get(module_name)
    if module is None:
        importlib.import_module(module_name)
        continue
    importlib.reload(module)

import maya_production_pipeliner.launcher as _launcher

_launcher.launch()
