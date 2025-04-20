import cv2
import os
import argparse
import time
import numpy as np
from PIL import Image

def capture_card_images(output_dir, camera_id=0, capture_delay=2, num_images=1):
    """
    Tool to help capture images of poker cards for training.
    
    Args:
        output_dir: Directory to save captured images
        camera_id: Camera device ID
        capture_delay: Delay between captures (seconds)
        num_images: Number of images to capture per card
    """
    # Ensure output directory exists
    print(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize camera
    cap = cv2.VideoCapture(camera_id)
    
    if not cap.isOpened():
        print(f"Error: Could not open camera {camera_id}")
        return
    
    try:
        while True:
            # Get card name from user
            card_name = input("\nEnter card name (e.g., ace_of_spades) or 'o' to quit: ")
            
            if card_name.lower() == 'o':
                break
            
            # Create directory for this card
            card_dir = os.path.join(output_dir, card_name)
            os.makedirs(card_dir, exist_ok=True)
            
            print(f"Place {card_name} in position. Press SPACE to capture or 'o' to skip.")
            print(f"Will capture {num_images} image(s) with {capture_delay}s delay.")
            
            # Main capture loop for this card
            images_captured = 0
            skip_card = False
            
            while images_captured < num_images and not skip_card:
                # Read frame
                ret, frame = cap.read()
                if not ret:
                    print("Error: Failed to capture frame")
                    break
                
                # Display frame with guides
                display_frame = frame.copy()
                h, w = display_frame.shape[:2]
                
                # Draw center crosshair
                cv2.line(display_frame, (w//2, 0), (w//2, h), (0, 255, 0), 1)
                cv2.line(display_frame, (0, h//2), (w, h//2), (0, 255, 0), 1)
                
                # Draw a rectangle to indicate card placement area
                card_w, card_h = int(w * 0.7), int(h * 0.7)
                start_x, start_y = (w - card_w) // 2, (h - card_h) // 2
                cv2.rectangle(display_frame, (start_x, start_y), 
                              (start_x + card_w, start_y + card_h), 
                              (0, 255, 0), 2)
                
                # Show info text
                cv2.putText(display_frame, f"Card: {card_name}", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(display_frame, f"Image {images_captured+1}/{num_images}", (10, 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(display_frame, "Press SPACE to capture, 'q' to skip", (10, 90), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 200), 2)
                
                cv2.imshow('Card Capture', display_frame)
                
                # Handle keypress
                key = cv2.waitKey(1) & 0xFF
                if key == ord(' '):  # Space key
                    # Capture image logic
                    timestamp = int(time.time())
                    img_path = os.path.join(card_dir, f"{card_name}_{timestamp}.jpg")
                    
                    # Save original frame
                    cv2.imwrite(img_path, frame)
                    print(f"Captured image {images_captured+1}/{num_images} saved to {img_path}")
                    
                    # Also save a preprocessed version for model input size
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_image = Image.fromarray(rgb_frame)
                    preproc_path = os.path.join(card_dir, f"{card_name}_{timestamp}_224x224.jpg")
                    pil_image.save(preproc_path)
                    
                    images_captured += 1
                    
                    # Wait if more images to capture
                    if images_captured < num_images:
                        print(f"Waiting {capture_delay}s for next capture...")
                        time.sleep(capture_delay)
                
                elif key == ord('o'):
                    skip_card = True
                    print(f"Skipped {card_name}")
            
            print(f"Completed capturing {images_captured} images for {card_name}")
    
    finally:
        # Release resources
        cap.release()
        cv2.destroyAllWindows()
        print("\nCard capture completed")

def main():
    parser = argparse.ArgumentParser(description="Capture card images for training")
    parser.add_argument('--output', type=str, default='card_images', 
                       help='Output directory for captured images')
    parser.add_argument('--camera', type=int, default=0, help='Camera ID to use')
    parser.add_argument('--delay', type=int, default=2, 
                       help='Delay between multiple captures (seconds)')
    parser.add_argument('--num', type=int, default=1, 
                       help='Number of images to capture per card')
    
    args = parser.parse_args()
    capture_card_images(args.output, args.camera, args.delay, args.num)

if __name__ == "__main__":
    main()