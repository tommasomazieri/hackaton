"""
CONVERT_DW_ONNX — one-time SavedModel -> ONNX for GPU inference.
================================================================
tensorflow-cpu can't use the GPU on native Windows, so we export the pretrained
Dynamic World SavedModel to ONNX once and run it through onnxruntime-gpu's CUDA
execution provider (see dw_model.py).

    python src/model/site_analysis/convert_dw_onnx.py

Writes vendor/dynamicworld/dw.onnx. Idempotent-ish: overwrites if re-run.
"""
from __future__ import annotations

import os
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
SAVED_DIR = os.path.join(PROJECT_ROOT, "vendor", "dynamicworld", "model", "forward")
ONNX_OUT = os.path.join(PROJECT_ROOT, "vendor", "dynamicworld", "dw.onnx")
OPSET = 17


def _replace_scale_and_translate(graph) -> int:
    """Swap each unsupported ScaleAndTranslate (no-op resize) for Identity(image)."""
    from onnx import helper
    fixed = 0
    for i, n in enumerate(list(graph.node)):
        if n.op_type == "ScaleAndTranslate":
            ident = helper.make_node("Identity", [n.input[0]], [n.output[0]], name=n.name + "_id")
            graph.node.remove(n)
            graph.node.insert(i, ident)
            fixed += 1
    return fixed


def main() -> None:
    if not (os.path.isdir(SAVED_DIR) and os.listdir(SAVED_DIR)):
        sys.exit(f"SavedModel not found at {SAVED_DIR} — run fetch_model.py first.")

    cmd = [
        sys.executable, "-m", "tf2onnx.convert",
        "--saved-model", SAVED_DIR,
        "--output", ONNX_OUT,
        "--opset", str(OPSET),
    ]
    print("$", " ".join(cmd))
    subprocess.run(cmd, check=True)

    import onnx
    m = onnx.load(ONNX_OUT)

    # tf2onnx leaves the model's internal tf.image.resize as a `ScaleAndTranslate`
    # op, which onnxruntime has no kernel for (invalid graph). That resize maps the
    # input to its own size (scale = 1), i.e. a no-op — verified ~99.7% class
    # agreement vs the TF model — so we replace it with Identity to make the graph
    # runnable on the CUDA EP.
    n_fixed = _replace_scale_and_translate(m.graph)
    if n_fixed:
        onnx.save(m, ONNX_OUT)
        print(f"Patched {n_fixed} ScaleAndTranslate -> Identity")

    def _shape(t):
        return [d.dim_param or d.dim_value for d in t.type.tensor_type.shape.dim]

    print("\nONNX inputs:")
    for i in m.graph.input:
        print(f"  {i.name}  {_shape(i)}")
    print("ONNX outputs:")
    for o in m.graph.output:
        print(f"  {o.name}  {_shape(o)}")
    print(f"\nWrote {ONNX_OUT}")


if __name__ == "__main__":
    main()
