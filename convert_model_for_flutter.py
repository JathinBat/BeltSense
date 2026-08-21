#!/usr/bin/env python3
"""
Export the trained YOLOv8 seat-belt classifier to ONNX for the Flutter app.

The app runs `assets/models/seatbelt_model.onnx` on-device via onnxruntime.
The exported contract, which lib/main.dart depends on, is:

    input  "images"  [1, 3, 224, 224]  float32, NCHW, RGB, scaled to 0-1
    output "output0" [1, 2]            softmax already applied by the model
    classes                            {0: no_seatbelt, 1: seatbelt}

Preprocessing that matches training: scale the shorter side to 224 preserving
aspect ratio, centre-crop 224x224, divide by 255. Do NOT subtract ImageNet
mean/std and do NOT convert to grayscale - both measurably reduce accuracy.

Note: an earlier version of this script also emitted `seatbelt_model.tflite`
built from a freshly-initialised Keras CNN whose weights were never loaded
from best.pt. That file was a random-weight stub, not the trained model, and
has been removed along with the code that produced it.
"""

import json
import os
import shutil
import sys

DEFAULT_WEIGHTS = "training_results/optimized_run_1759628547/weights/best.pt"
OUTPUT_DIR = "seatbelt_detector_app/assets/models"
IMGSZ = 224
CLASS_NAMES = ["no_seatbelt", "seatbelt"]


def export_onnx(weights: str, output_dir: str) -> str:
    """Export `weights` to ONNX and copy it into the app's assets."""
    from ultralytics import YOLO

    if not os.path.exists(weights):
        raise FileNotFoundError(f"Model file not found: {weights}")

    os.makedirs(output_dir, exist_ok=True)

    print(f"Loading {weights}")
    model = YOLO(weights)

    print(f"Exporting to ONNX at {IMGSZ}x{IMGSZ} ...")
    exported = model.export(format="onnx", imgsz=IMGSZ, simplify=True)

    # Recent ultralytics returns the export path; older versions write
    # best.onnx next to the weights.
    if not (exported and os.path.exists(str(exported))):
        exported = os.path.join(os.path.dirname(weights), "best.onnx")
    if not os.path.exists(str(exported)):
        raise RuntimeError("ONNX export did not produce a file")

    destination = os.path.join(output_dir, "seatbelt_model.onnx")
    shutil.copy(str(exported), destination)
    print(f"Wrote {destination}")
    return destination


def verify_onnx(path: str) -> dict:
    """Fail loudly if the export does not match the contract main.dart expects."""
    import onnx

    graph = onnx.load(path).graph

    def dims(value):
        return [d.dim_value or d.dim_param for d in value.type.tensor_type.shape.dim]

    inputs = {v.name: dims(v) for v in graph.input}
    outputs = {v.name: dims(v) for v in graph.output}

    if inputs.get("images") != [1, 3, IMGSZ, IMGSZ]:
        raise RuntimeError(f"Unexpected input signature: {inputs}")
    if outputs.get("output0") != [1, len(CLASS_NAMES)]:
        raise RuntimeError(f"Unexpected output signature: {outputs}")

    print(f"Verified: images {inputs['images']} -> output0 {outputs['output0']}")
    return {"inputs": inputs, "outputs": outputs}


def write_model_info(output_dir: str) -> None:
    info = {
        "model_name": "seatbelt_classifier",
        "file": "seatbelt_model.onnx",
        "architecture": "yolov8n-cls",
        "input_name": "images",
        "input_shape": [1, 3, IMGSZ, IMGSZ],
        "input_layout": "NCHW",
        "colour": "RGB",
        "normalization": "divide by 255 only; no mean/std subtraction",
        "resize": (
            "scale shorter side to 224 preserving aspect ratio, "
            "then centre-crop 224x224"
        ),
        "output_name": "output0",
        "output_shape": [1, len(CLASS_NAMES)],
        "output_note": (
            "softmax is already applied inside the model; do not apply it again"
        ),
        "class_names": CLASS_NAMES,
    }
    path = os.path.join(output_dir, "model_info.json")
    with open(path, "w") as handle:
        json.dump(info, handle, indent=2)
        handle.write("\n")
    print(f"Wrote {path}")


def main() -> int:
    weights = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_WEIGHTS
    try:
        destination = export_onnx(weights, OUTPUT_DIR)
        verify_onnx(destination)
        write_model_info(OUTPUT_DIR)
    except Exception as error:  # noqa: BLE001 - surface the reason to the user
        print(f"\nExport failed: {error}")
        return 1
    print("\nExport complete. Run the app to use the trained model.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
