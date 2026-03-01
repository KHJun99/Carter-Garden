Quick steps to produce and use TensorRT engine (monkey_model.engine)

1) Export TorchScript to ONNX

```bash
python3 export_to_onnx.py
```

This writes `monkey_model.onnx` (dummy input 1x3x480x640).

2) (Optional) Simplify ONNX

```bash
# pip3 install onnx onnx-simplifier
python3 -m onnxsim monkey_model.onnx monkey_model_sim.onnx
```

3) Build TensorRT engine (Jetson에서 FP16 권장)

```bash
chmod +x build_trt_engine.sh
./build_trt_engine.sh monkey_model.onnx monkey_model.engine
```

4) `detector_monkey_node.py`는 우선적으로 `models/monkey_model.engine`을 시도하여 로드합니다.
   - 엔진이 없으면 `models/yolo11n.pt`로 폴백합니다.