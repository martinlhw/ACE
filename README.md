# ACE
Carnegie Mellon ECE Capstone, Spring 2025

## Quick Start

### Data Collection

1. Capture card images:
```bash
cd train
python capture_data.py --output ../data/
```

### Training
```bash
python src/run_training.sh
```
### Inference
```bash
python src/run_inference.sh
```