import cv2
import os
import argparse
import time
import numpy as np
from PIL import Image
from picamera2 import Picamera2
import threading

def capture_card_images(output_dir, capture_delay=2, num_images=1):
    """
    Tool to help capture images of poker cards for training using Picamera2.
    
    Args:
        output_dir: Directory to save captured images
        capture_delay: Delay between captures (seconds)
        num_images: Number of images to capture per card
    """
    # Ensure output directory exists
    print(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    # Environment variables for OpenCV display
    os.environ["QT_QPA_PLATFORM"] = "xcb"
    os.environ["GDK_BACKEND"] = "x11"
    
    # Initialize Picamera2
    picam2 = Picamera2()
    picam2.configure(picam2.create_preview_configuration(main={"size": (640, 480), "format": "BGR888"}))
    picam2.start()
    time.sleep(2)  # Give camera time to initialize
    
    # Flag for display thread
    stop_display_thread = False
    current_stage = "naming"  # Can be "naming" or "capturing"
    card_name = ""
    
    # Function to continuously update display
    def update_display():
        while not stop_display_thread:
            # Capture and display frame
            frame = picam2.capture_array()
            
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
            
            # Show info text based on current stage
            if current_stage == "naming":
                cv2.putText(display_frame, "Place card in view", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(display_frame, "Enter class name in terminal", (10, 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            else:  # capturing
                cv2.putText(display_frame, f"Card: {card_name}", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(display_frame, "Press SPACE+ENTER to capture", (10, 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Display using OpenCV
            cv2.namedWindow('Card Capture', cv2.WINDOW_NORMAL)
            cv2.imshow('Card Capture', display_frame)
            cv2.waitKey(1)  # Just update the display
            
            time.sleep(0.03)  # ~30fps update rate
    
    try:
        print("\nStarting card capture session. Place cards on the camera and classify them.")
        print("Press 'q' to quit the session when finished.")
        
        # Start display thread
        display_thread = threading.Thread(target=update_display)
        display_thread.daemon = True
        display_thread.start()
        
        while True:
            # Let the user see the card in the continuously updating display
            # and directly ask for name
            nonlocal_card_name = input("\nEnter card name (e.g., ace_of_spades) or 'q' to quit: ")
            
            if nonlocal_card_name.lower() == 'q':
                break
            
            # Update the card name for display
            card_name = nonlocal_card_name
            current_stage = "capturing"
            
            # Create directory for this card
            card_dir = os.path.join(output_dir, card_name)
            os.makedirs(card_dir, exist_ok=True)
            
            print(f"Card identified as {card_name}.")
            print(f"Will capture {num_images} image(s) with {capture_delay}s delay.")
            
            # Main capture loop for this card
            images_captured = 0
            skip_card = False
            
            while images_captured < num_images and not skip_card:
                # Get keyboard input for this frame
                key = input("Press SPACE then ENTER to capture, or 'q' to skip: ")
                
                if key == ' ':
                    # Capture latest frame
                    frame = picam2.capture_array()
                    
                    # Capture image logic
                    timestamp = int(time.time())
                    img_path = os.path.join(card_dir, f"{card_name}_{timestamp}.jpg")
                    
                    # Save original frame
                    cv2.imwrite(img_path, frame)
                    print(f"Captured image {images_captured+1}/{num_images} saved to {img_path}")
                    
                    # Also save a preprocessed version for model input size
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_image = Image.fromarray(rgb_frame)
                    preproc_image = pil_image.resize((224, 224))
                    preproc_path = os.path.join(card_dir, f"{card_name}_{timestamp}_224x224.jpg")
                    preproc_image.save(preproc_path)
                    
                    images_captured += 1
                    
                    # Wait if more images to capture
                    if images_captured < num_images:
                        print(f"Waiting {capture_delay}s for next capture...")
                        time.sleep(capture_delay)
                    else:
                        break  # Break out of the inner loop when all images are captured
                elif key.lower() == 'q':
                    skip_card = True
                    print(f"Skipped {card_name}")
            
            print(f"Completed capturing {images_captured} images for {card_name}")
            
            # Reset for next card
            current_stage = "naming"
            card_name = ""
    
    finally:
        # Signal the display thread to stop and wait for it to finish
        stop_display_thread = True
        if 'display_thread' in locals() and display_thread.is_alive():
            display_thread.join(timeout=1.0)
            
        # Release resources
        picam2.stop()
        cv2.destroyAllWindows()
        print("\nCard capture completed")

def main():
    parser = argparse.ArgumentParser(description="Capture card images for training")
    parser.add_argument('--output', type=str, default='card_images', 
                       help='Output directory for captured images')
    parser.add_argument('--delay', type=int, default=2, 
                       help='Delay between multiple captures (seconds)')
    parser.add_argument('--num', type=int, default=1, 
                       help='Number of images to capture per card')
    
    args = parser.parse_args()
    capture_card_images(args.output, args.delay, args.num)

if __name__ == "__main__":
    main()