import cv2
import torch
import numpy as np
import time
import argparse
import os
from PIL import Image
import torchvision.transforms as transforms
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from train.model import PokerCardClassifier, create_optimizer

def load_model(checkpoint_path, num_classes=52, device='cpu'):
    """
    Load a saved model from checkpoint.
    
    Args:
        checkpoint_path: Path to the saved model checkpoint
        num_classes: Number of card classes
        device: Device to load the model on
        
    Returns:
        Loaded model
    """
    model = PokerCardClassifier(num_classes)
    
    # Load checkpoint
    checkpoint = torch.load(checkpoint_path, map_location=device)
    
    # Handle different checkpoint formats
    if 'model_state_dict' in checkpoint:
        model.load_state_dict(checkpoint['model_state_dict'])
    else:
        model.load_state_dict(checkpoint)
        
    model = model.to(device)
    return model

class RealtimeCardDetector:
    """
    Real-time poker card detector using a pre-trained model.
    Processes video frames from a camera and classifies cards.
    """
    def __init__(self, model_path, class_names, device='cpu', 
                 input_size=(224, 224), confidence_threshold=0.7, fps_avg_frames=10):
        """
        Initialize the detector.
        
        Args:
            model_path: Path to the trained model
            class_names: List of class names
            device: Device to run inference on
            input_size: Input size for the model
            confidence_threshold: Minimum confidence to display predictions
            fps_avg_frames: Number of frames to average FPS calculation
        """
        self.device = device
        self.class_names = class_names
        self.input_size = input_size
        self.confidence_threshold = confidence_threshold
        
        # Load model
        self.model = self._load_model(model_path)
        self.model.eval()
        
        # Create transform for preprocessing
        self.transform = transforms.Compose([
            transforms.Resize(input_size),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        # FPS calculation
        self.fps_avg_frames = fps_avg_frames
        self.frame_times = []
        
        print(f"Model loaded successfully. Ready to detect {len(class_names)} card types.")
        
    def _load_model(self, model_path):
        """Load the model from checkpoint."""
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
                
        # Load model
        return load_model(
            checkpoint_path=model_path,
            num_classes=len(self.class_names),
            device=self.device
        )
    
    def preprocess_frame(self, frame):
        """
        Preprocess a video frame for the model.
        
        Args:
            frame: Input BGR frame from OpenCV
            
        Returns:
            Preprocessed tensor ready for model input
        """
        # convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # convert to PIL Image
        pil_image = Image.fromarray(rgb_frame)
        
        # Apply transformations
        tensor = self.transform(pil_image).unsqueeze(0).to(self.device)
        
        return tensor
    
    def predict(self, frame):
        """
        Predict the card class from a frame.
        
        Args:
            frame: Input BGR frame from OpenCV
            
        Returns:
            class_name: Predicted class name
            confidence: Confidence score (0-100%)
        """
        # Preprocess the frame
        tensor = self.preprocess_frame(frame)
        
        # Run inference
        with torch.no_grad():
            outputs = self.model(tensor)
            probabilities = torch.nn.functional.softmax(outputs, dim=1)
            confidence, prediction = torch.max(probabilities, 1)
        
        class_name = self.class_names[prediction.item()]
        confidence_value = confidence.item() * 100
        
        return class_name, confidence_value
    
    def update_fps(self):
        """Update FPS calculation."""
        current_time = time.time()
        self.frame_times.append(current_time)
        
        # Keep only the last n frames for averaging
        if len(self.frame_times) > self.fps_avg_frames:
            self.frame_times.pop(0)
        
        # Calculate FPS
        if len(self.frame_times) > 1:
            time_diff = self.frame_times[-1] - self.frame_times[0]
            if time_diff > 0:
                return (len(self.frame_times) - 1) / time_diff
        return 0
    
    def run(self, camera_id=0, display_scale=1.0):
        """
        Run the detector on live video feed.
        
        Args:
            camera_id: Camera ID to use
            display_scale: Scale factor for display window
        """
        # Initialize video capture
        cap = cv2.VideoCapture(camera_id)
        
        # Check if camera opened successfully
        if not cap.isOpened():
            print(f"Error: Could not open camera {camera_id}")
            return
        
        print(f"Starting real-time detection with camera {camera_id}")
        print("Press 'q' to quit")
        
        while True:
            # capture a frame from the camera (succes, np.ndarray)
            success, frame = cap.read() # h x w x c (BGR format)
            if not success:
                print("Error: Failed to capture frame")
                break
            
            # get prediction
            class_name, confidence = self.predict(frame)
            
            # Calculate FPS
            fps = self.update_fps()
            
            # Display information on frame
            info_frame = frame.copy()
            
            # Display prediction if confidence is above threshold
            if confidence >= self.confidence_threshold:
                cv2.putText(info_frame, f"Card: {class_name}", (10, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                cv2.putText(info_frame, f"Conf: {confidence:.1f}%", (10, 70), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            else:
                cv2.putText(info_frame, "No card detected", (10, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
            
            # Display FPS
            cv2.putText(info_frame, f"FPS: {fps:.1f}", (10, 110), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            
            # Resize the display window if needed
            if display_scale != 1.0:
                width = int(info_frame.shape[1] * display_scale)
                height = int(info_frame.shape[0] * display_scale)
                display_frame = cv2.resize(info_frame, (width, height))
            else:
                display_frame = info_frame
            
            # Show the frame
            cv2.imshow('Poker Card Detection', display_frame)
            
            # Exit on 'q' key press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        # Release resources
        cap.release()
        cv2.destroyAllWindows()
        print("Detection ended")


def load_class_names(class_file):
    """Load class names from a text file."""
    if not os.path.exists(class_file):
        raise FileNotFoundError(f"Class names file not found: {class_file}")
        
    with open(class_file, 'r') as f:
        return [line.strip() for line in f.readlines()]


def main():
    parser = argparse.ArgumentParser(description="Real-time Poker Card Detector")
    parser.add_argument('--model', type=str, required=True, help='Path to trained model')
    parser.add_argument('--classes', type=str, required=True, help='Path to class names file')
    parser.add_argument('--camera', type=int, default=0, help='Camera ID to use')
    parser.add_argument('--threshold', type=float, default=0.7, help='Confidence threshold')
    parser.add_argument('--display_scale', type=float, default=1.0, help='Display window scale factor')
    parser.add_argument('--device', type=str, default='cpu', help='Device to use (cpu/cuda)')

    args = parser.parse_args()
    
    print("Starting Poker Card Detection System")
    
    try:
        # Load class names
        print(f"Loading class names from {args.classes}")
        class_names = load_class_names(args.classes)
        print(f"Loaded {len(class_names)} card classes")
        
        # Initialize detector
        print(f"Loading model from {args.model}")
        detector = RealtimeCardDetector(
            model_path=args.model,
            class_names=class_names,
            device=args.device,
            confidence_threshold=args.threshold
        )
        
        # Run detection
        detector.run(camera_id=args.camera, display_scale=args.display_scale)
    
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()