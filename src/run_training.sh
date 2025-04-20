#!/bin/bash

PROJECT_ROOT="$(pwd)"
cd "$PROJECT_ROOT"
# default params
DATA_DIR="/Users/martinlee/academics_archive/18500/ACE/data/"
OUTPUT_DIR="${PROJECT_ROOT}/models"  # Use absolute path
NUM_EPOCHS=100
BATCH_SIZE=32
DEVICE="cpu" # GPU not needed as training sample small

# print banner
echo "=========================================="
echo "      Poker Card Classifier Training      "
echo "=========================================="
echo ""

# Python check
if ! command -v python3 &> /dev/null; then
    echo "Python 3 not found. Please install Python 3."
    exit 1
fi

# DATA_DIR check
if [ ! -d "$DATA_DIR" ]; then
    echo "Error: Data directory not found at $DATA_DIR"
    echo "Please update the DATA_DIR variable or capture images first."
    exit 1
fi


# OUTPUT_DIR check; create if not exists
if [ ! -d "$OUTPUT_DIR" ]; then
    echo "Creating output directory: $OUTPUT_DIR"
    mkdir -p "$OUTPUT_DIR"
fi

# prepare class names file
CLASS_FILE="${PROJECT_ROOT}/data/class_names.txt"
echo "Generating class names file..."
python3 train/prepare_classes.py --data_dir "$DATA_DIR" --output "$CLASS_FILE"

echo "Starting training with:"
echo "- Data: $DATA_DIR"
echo "- Output: $OUTPUT_DIR"
echo "- Type: $TRAIN_TYPE"
echo "- Epochs: $NUM_EPOCHS"
echo "- Device: $DEVICE"
echo ""

# start training
python3 train/main.py \
    --data_dir "$DATA_DIR" \
    --output_dir "$OUTPUT_DIR" \
    --num_epochs $NUM_EPOCHS \
    --batch_size $BATCH_SIZE \
    --repetitions 100

BEST_MODEL_PATH="$OUTPUT_DIR/checkpoints/best_model.pth"

if [ -f "$BEST_MODEL_PATH" ]; then
    cp "$BEST_MODEL_PATH" "$OUTPUT_DIR/best_model.pth"
    echo "Best model copied to $OUTPUT_DIR/best_model.pth"
fi

# Exit message
echo ""
echo "Training completed. Model saved to $OUTPUT_DIR"