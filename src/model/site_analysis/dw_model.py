"""
DW_MODEL — local inference with the pretrained Google Dynamic World CNN.
=======================================================================
Loads the TensorFlow SavedModel shipped in google/dynamicworld (`model/forward`)
and runs it on a Sentinel-2 L2A surface-reflectance array. No Earth Engine.

Preprocessing mirrors the repo's single_image_runner.ipynb exactly:
  1. log scaling:        x = log(x * 0.005 + 1)
  2. percentile norm:    x = (x - NORM_PERCENTILES[:,0]) / NORM_PERCENTILES[:,1]
  3. sigmoid transfer:   x = exp(x*5 - 1); x = x / (x + 1)

Input bands, in order: B2 B3 B4 B5 B6 B7 B8 B11 B12  (9 bands).
The model is fully convolutional; we still tile to a fixed window to bound memory.
TensorFlow is imported lazily so the rest of the package imports without it.
"""
from __future__ import annotations

import os

import numpy as np

# Verified from google/dynamicworld single_image_runner.ipynb (30th/70th pct per band).
NORM_PERCENTILES = np.array([
    [1.7417, 2.0233], [1.7261, 2.0389], [1.6798, 2.1796],
    [1.7735, 2.2890], [2.2892, 2.6172], [2.3829, 2.7734],
    [2.3829, 2.7578], [2.1952, 2.7891], [1.5548, 2.4141],
], dtype=np.float32)

S2_BANDS = ["B2", "B3", "B4", "B5", "B6", "B7", "B8", "B11", "B12"]
PATCH = 399          # native DW window (~4 km at 10 m)
DEFAULT_MODEL_DIR = os.path.join("vendor", "dynamicworld", "model", "forward")

_HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
DEFAULT_ONNX = os.path.join(PROJECT_ROOT, "vendor", "dynamicworld", "dw.onnx")

_model = None         # cached TF SavedModel singleton
_ort_session = None   # cached onnxruntime session singleton
_ort_in = None
_ort_out = None
_onnx_failed = False   # set True if the ONNX path errors once -> stick to TF


# ---------------------------------------------------------------------------
# ONNX Runtime (GPU) backend — preferred when dw.onnx + onnxruntime are present.
# tensorflow-cpu can't use the GPU on native Windows, so we run the exported ONNX
# graph on the NVIDIA card via the CUDA execution provider.
# ---------------------------------------------------------------------------
def _add_cuda_dll_dirs() -> None:
    """Expose the pip-installed NVIDIA CUDA/cuDNN DLLs to onnxruntime (Windows).

    onnxruntime_providers_cuda.dll depends on cublasLt/cudnn/cufft DLLs that the
    nvidia-*-cu12 wheels drop in site-packages/nvidia/<lib>/bin. Add them all to
    the DLL search path before the CUDA provider loads."""
    if os.name != "nt":
        return
    import glob
    bins: set[str] = set()
    try:  # most reliable inside a venv — locate the actual installed package
        import nvidia
        base = os.path.dirname(nvidia.__file__)
        bins.update(glob.glob(os.path.join(base, "*", "bin")))
    except Exception:
        pass
    import site
    roots = []
    try:
        roots += list(site.getsitepackages())
    except Exception:
        pass
    try:
        roots.append(site.getusersitepackages())
    except Exception:
        pass
    for root in roots:
        bins.update(glob.glob(os.path.join(root, "nvidia", "*", "bin")))
    path_parts = []
    for binp in bins:
        if os.path.isdir(binp):
            try:
                os.add_dll_directory(binp)
            except Exception:
                pass
            path_parts.append(binp)
    if path_parts:  # PATH covers transitive DLL deps (cublasLt -> ...) that add_dll_directory misses
        os.environ["PATH"] = os.pathsep.join(path_parts) + os.pathsep + os.environ.get("PATH", "")


def _onnx_available() -> bool:
    """True if we should use the ONNX/GPU path (file present, ORT installed, not disabled)."""
    if os.environ.get("DW_BACKEND", "").lower() == "tf":
        return False
    path = os.environ.get("DW_ONNX", DEFAULT_ONNX)
    if not os.path.exists(path):
        return False
    import importlib.util
    return importlib.util.find_spec("onnxruntime") is not None


def load_onnx():
    """Load (and cache) the ONNX session with CUDA first, CPU fallback."""
    global _ort_session, _ort_in, _ort_out
    if _ort_session is not None:
        return _ort_session
    import onnxruntime as ort

    _add_cuda_dll_dirs()
    if hasattr(ort, "preload_dlls"):  # ORT >=1.20 loads CUDA/cuDNN from the nvidia wheels
        try:
            ort.preload_dlls()
        except Exception as exc:
            print(f"[dw_model] preload_dlls warning: {exc}")
    path = os.environ.get("DW_ONNX", DEFAULT_ONNX)
    providers = [("CUDAExecutionProvider", {}), "CPUExecutionProvider"]
    _ort_session = ort.InferenceSession(path, providers=providers)
    _ort_in = _ort_session.get_inputs()[0].name
    _ort_out = _ort_session.get_outputs()[0].name
    print(f"[dw_model] ONNX session active, providers: {_ort_session.get_providers()}")
    return _ort_session


def preprocess(image: np.ndarray) -> np.ndarray:
    """Apply the DW band normalization. `image` is (..., 9) surface reflectance."""
    x = np.asarray(image, dtype=np.float32)
    x = np.log(x * 0.005 + 1.0)
    x = (x - NORM_PERCENTILES[:, 0]) / NORM_PERCENTILES[:, 1]
    x = np.exp(x * 5.0 - 1.0)
    x = x / (x + 1.0)
    return x.astype(np.float32)


def load_model(model_dir: str | None = None):
    """Load (and cache) the forward SavedModel. Lazy-imports TensorFlow."""
    global _model
    if _model is not None:
        return _model
    import tensorflow as tf  # lazy: heavy, optional dep

    path = model_dir or os.environ.get("DW_MODEL_DIR", DEFAULT_MODEL_DIR)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Dynamic World SavedModel not found at '{path}'. "
            "Run: python src/model/site_analysis/fetch_model.py"
        )
    _model = tf.saved_model.load(path)
    return _model


def _infer_window(model, window: np.ndarray) -> np.ndarray:
    """Run the model on one preprocessed (H, W, 9) window -> (H, W, 9) class probs."""
    import tensorflow as tf

    batch = tf.convert_to_tensor(window[np.newaxis, ...], dtype=tf.float32)
    out = model(batch)
    if isinstance(out, dict):
        out = next(iter(out.values()))
    return np.asarray(out)[0]


def predict(bands: np.ndarray, window: int = PATCH, overlap: int = 32) -> np.ndarray:
    """Tile a large S2 array and run DW, returning a (H, W) int8 class raster.

    Uses the ONNX/GPU backend when available (dw.onnx + onnxruntime), else the
    TensorFlow SavedModel. A broken/invalid ONNX file falls back to TF, never
    crashes the request. Band order = S2_BANDS.
    """
    global _onnx_failed
    if _onnx_available() and not _onnx_failed:
        try:
            return _predict_onnx(bands, window, overlap)
        except Exception as exc:
            print(f"[dw_model] ONNX backend failed ({exc}); falling back to TF CPU")
            _onnx_failed = True
    return _predict_tf(bands, window, overlap)


def _tile_iter(H: int, W: int, window: int, overlap: int):
    """Yield (r0c, r1, c0c, c1) full-size (where possible) tile windows."""
    step = window - overlap
    for r0 in range(0, H, step):
        for c0 in range(0, W, step):
            r1, c1 = min(r0 + window, H), min(c0 + window, W)
            r0c, c0c = max(0, r1 - window), max(0, c1 - window)
            yield r0c, r1, c0c, c1
            if c1 >= W:
                break
        if r1 >= H:
            break


def _accumulate(probs_for, bands, window, overlap):
    """Shared tiling + overlap-averaging; `probs_for(tile)->(h,w,9)` runs a backend."""
    H, W, C = bands.shape
    assert C == len(S2_BANDS), f"expected {len(S2_BANDS)} bands, got {C}"
    prob_sum = np.zeros((H, W, 9), dtype=np.float32)
    weight = np.zeros((H, W, 1), dtype=np.float32)
    for r0c, r1, c0c, c1 in _tile_iter(H, W, window, overlap):
        prob_sum[r0c:r1, c0c:c1, :] += probs_for(bands[r0c:r1, c0c:c1, :])
        weight[r0c:r1, c0c:c1, :] += 1.0
    weight[weight == 0] = 1.0
    return (prob_sum / weight).argmax(axis=-1).astype(np.int8)


def _predict_tf(bands: np.ndarray, window: int = PATCH, overlap: int = 32) -> np.ndarray:
    model = load_model()
    return _accumulate(lambda tile: _infer_window(model, preprocess(tile)), bands, window, overlap)


def _predict_onnx(bands: np.ndarray, window: int = PATCH, overlap: int = 32) -> np.ndarray:
    sess = load_onnx()

    def _run(tile):
        x = preprocess(tile)[np.newaxis, ...].astype(np.float32)
        return sess.run([_ort_out], {_ort_in: x})[0][0]

    return _accumulate(_run, bands, window, overlap)
