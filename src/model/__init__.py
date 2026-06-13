"""src.model — importlib shims for numbered script files."""
import importlib.util
import os

_HERE = os.path.dirname(os.path.abspath(__file__))


def _load(filename: str):
    name = filename.replace(".py", "").replace("-", "_")
    spec = importlib.util.spec_from_file_location(name, os.path.join(_HERE, filename))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


load_filter = _load("01_load_filter.py")
compute = _load("02_compute.py")
rank = _load("03_rank.py")

# Stage 4 (CNN site analysis) pulls a heavy optional stack (TF / STAC / rasterio).
# Load it defensively so the API still boots when those deps are absent — callers
# must treat `site_stage is None` as "site analysis unavailable".
try:
    site_stage = _load("04_site_analysis.py")
    site_stage_error = None
except Exception as _exc:  # missing optional deps, bad model path, etc.
    site_stage = None
    site_stage_error = str(_exc)
