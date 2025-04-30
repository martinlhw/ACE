#!/bin/bash
#!/bin/bash

# Run real-time poker card detection
# This script makes it easy to run the inference code

# Default parameters
PROJECT_ROOT="$(pwd)"
MODEL_PATH="${PROJECT_ROOT}/models/best_model.pth"
CLASS_FILE="${PROJECT_ROOT}/data/class_names.txt"
CAMERA_ID=0 # default camera
DEVICE="cpu"
THRESHOLD=0.7
DISPLAY_SCALE=1.0

# print banner
echo "=========================================="
echo "   Poker Card Real-time Detection System  "
echo "=========================================="
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Python 3 not found. Please install Python 3."
    exit 1
fi

# Check if model file exists
if [ ! -f "$MODEL_PATH" ]; then
    echo "Error: Model file not found at $MODEL_PATH"
    echo "Please update the MODEL_PATH variable or train a model first."
    exit 1
fi

# Check if class file exists
if [ ! -f "$CLASS_FILE" ]; then
    echo "Error: Class names file not found at $CLASS_FILE"
    echo "Please update the CLASS_FILE variable or generate class names first."
    exit 1
fi

echo "Starting detection with:"
echo "- Model: $MODEL_PATH"
echo "- Classes: $CLASS_FILE"
echo "- Camera: $CAMERA_ID"
echo "- Device: $DEVICE"
echo ""

# Run the detection script
python3 inference/realtime_detection.py \
    --model "$MODEL_PATH" \
    --classes "$CLASS_FILE" \
    --device "$DEVICE" \
    --threshold $THRESHOLD \
    --display_scale $DISPLAY_SCALE

# Exit message
echo ""
echo "Detection session ended."