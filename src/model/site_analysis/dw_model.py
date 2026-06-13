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

_model = None  # cached singleton


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
    """Tile a large S2 array and run DW, returning a class-index raster.

    Args:
        bands    (H, W, 9) Sentinel-2 surface reflectance, band order = S2_BANDS.
        window   tile side length in pixels.
        overlap  tile overlap to suppress seam artifacts; center crop is kept.

    Returns:
        (H, W) int8 raster of argmax DW class indices (0..8).
    """
    model = load_model()
    H, W, C = bands.shape
    assert C == len(S2_BANDS), f"expected {len(S2_BANDS)} bands, got {C}"

    prob_sum = np.zeros((H, W, 9), dtype=np.float32)
    weight = np.zeros((H, W, 1), dtype=np.float32)
    step = window - overlap

    for r0 in range(0, H, step):
        for c0 in range(0, W, step):
            r1, c1 = min(r0 + window, H), min(c0 + window, W)
            r0c, c0c = max(0, r1 - window), max(0, c1 - window)
            tile = bands[r0c:r1, c0c:c1, :]
            probs = _infer_window(model, preprocess(tile))
            prob_sum[r0c:r1, c0c:c1, :] += probs
            weight[r0c:r1, c0c:c1, :] += 1.0
            if c1 >= W:
                break
        if r1 >= H:
            break

    weight[weight == 0] = 1.0
    probs = prob_sum / weight
    return probs.argmax(axis=-1).astype(np.int8)
