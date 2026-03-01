#!/bin/bash
set -e

# Usage: ./build_trt_engine.sh monkey_model.onnx
ONNX=${1:-monkey_model.onnx}
ENGINE=${2:-monkey_model.engine}
WORKSPACE=2048

if ! command -v trtexec &> /dev/null; then
  echo "trtexec not found in PATH. Ensure TensorRT is installed and trtexec is available."
  exit 1
fi

echo "Simplifying ONNX (if onnxsim installed)..."
python3 -c "import onnx, sys; print('onnx available')" 2>/dev/null || true
if python3 -c "import onnxsim" 2>/dev/null; then
  onnxsim ${ONNX} ${ONNX%.onnx}_sim.onnx || true
  SIM_ONNX=${ONNX%.onnx}_sim.onnx
else
  SIM_ONNX=${ONNX}
fi

echo "Building TensorRT engine from ${SIM_ONNX} -> ${ENGINE} (FP16)"
trtexec --onnx=${SIM_ONNX} --saveEngine=${ENGINE} --fp16 --workspace=${WORKSPACE}

echo "Engine saved to ${ENGINE}"
