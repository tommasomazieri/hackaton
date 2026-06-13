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
