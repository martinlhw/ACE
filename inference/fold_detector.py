#!/usr/bin/env python3
import cv2
import numpy as np
import time
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from picamera2 import Picamera2  # Use Picamera2 for Raspberry Pi Camera Module

class FoldDetector:
    """
    Simple fold detector that identifies when a player folds by detecting any objects (cards)
    in a designated area on the poker table.
    """
    def __init__(self, camera_id=0, fold_area_coords=None, 
                 detection_threshold=500, fold_cooldown=2.0,
                 motion_sensitivity=20):
        """
        Initialize the fold detector.
        
        Args:
            camera_id: Not used with Picamera2—but kept for interface consistency.
            fold_area_coords: Coordinates for the fold area (x, y, width, height).
            detection_threshold: Minimum area of motion to consider a fold.
            fold_cooldown: Cooldown between fold detections (seconds).
            motion_sensitivity: Sensitivity for motion detection.
        """
        # Initialize Picamera2; note that camera selection can be more advanced if needed.
        try:
            self.cap = Picamera2()
            config = self.cap.create_preview_configuration(
                main={"format": "BGR888", "size": (640, 480)}
            )
            self.cap.configure(config)
            self.cap.start()
            print("Picamera2 initialized successfully.")
        except Exception as e:
            raise Exception(f"Could not initialize Picamera2: {e}")
        
        # Define fold area (if not provided, we'll set it interactively)
        self.fold_area_coords = fold_area_coords
        
        # Detection parameters
        self.detection_threshold = detection_threshold
        self.motion_sensitivity = motion_sensitivity
        
        # Fold event management
        self.fold_cooldown = fold_cooldown
        self.last_fold_time = 0
        
        # Initialize background subtractor for motion detection (unused in our current method)
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=100, varThreshold=self.motion_sensitivity, detectShadows=False
        )
        
        # Initialize background frame for the fold area
        self.background = None
        self.is_background_initialized = False
            
    def setup_fold_area(self):
        """Interactive setup to define the designated fold area on the table."""
        print("Let's define the fold area on the poker table.")
        print("Capturing a frame from the camera...")
        
        frame = self.cap.capture_array()
        if frame is None:
            raise Exception("Could not capture frame from camera during fold area setup")
            
        # Display frame and let user select rectangular region
        cv2.imshow("Define Fold Area", frame)
        self.fold_area_coords = cv2.selectROI("Define Fold Area", frame, False)
        cv2.destroyWindow("Define Fold Area")
        
        print(f"Fold area set to: {self.fold_area_coords}")
        
        # Initialize background after area selection
        self.initialize_background()
    
    def initialize_background(self, num_frames=30):
        """Initialize background model using the average of several frames."""
        print("Initializing background model...")
        print("Please ensure the fold area is empty...")
        
        if not self.fold_area_coords:
            raise ValueError("Fold area must be defined before initializing background")
        
        x, y, w, h = self.fold_area_coords
        frames = []
        
        # Collect frames for background averaging
        for i in range(num_frames):
            frame = self.cap.capture_array()
            if frame is None:
                raise Exception("Could not capture frame from camera during background initialization")
            
            # Extract fold area
            roi = frame[y:y+h, x:x+w]
            frames.append(roi)
            
            # Display progress
            progress_frame = frame.copy()
            cv2.rectangle(progress_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(
                progress_frame, f"Initializing: {i+1}/{num_frames}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2
            )
            cv2.imshow("Initializing Background", progress_frame)
            cv2.waitKey(1)
        
        # Compute the average background frame
        self.background = np.mean(frames, axis=0).astype(np.uint8)
        self.is_background_initialized = True
        
        cv2.destroyWindow("Initializing Background")
        print("Background initialized successfully.")
    
    def detect_fold_event(self, frame):
        """Detect if a fold event has occurred by comparing against the background."""
        if not self.fold_area_coords or not self.is_background_initialized:
            return False
        
        # Extract fold area from current frame
        x, y, w, h = self.fold_area_coords
        roi = frame[y:y+h, x:x+w]
        
        # Convert to grayscale
        roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        bg_gray = cv2.cvtColor(self.background, cv2.COLOR_BGR2GRAY)
        
        # Calculate absolute difference
        diff = cv2.absdiff(roi_gray, bg_gray)
        
        # Apply threshold to obtain a binary difference image
        _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
        
        # Apply morphology to remove small noise
        kernel = np.ones((5, 5), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        
        # Sum the changed pixels
        changed_pixels = np.sum(thresh > 0)
        total_pixels = w * h
        change_percent = (changed_pixels / total_pixels) * 100
        
        # If the change exceeds our threshold and the cooldown passed, register a fold event
        if changed_pixels > self.detection_threshold:
            current_time = time.time()
            if current_time - self.last_fold_time > self.fold_cooldown:
                self.last_fold_time = current_time
                print(f"Change detected: {changed_pixels} pixels ({change_percent:.2f}%)")
                return True
        
        return False
    
    def notify_game_state_manager(self, player_id=None):
        """Send a fold event to the game state manager (currently just prints a message)."""
        print(f"FOLD EVENT: Player {player_id if player_id else 'unknown'} has folded")
        # Here you would integrate with your game management system.
        return True
    
    def run(self, player_id=None, display=True):
        """
        Main loop for real-time fold detection.
        
        Args:
            player_id: ID of the player being monitored (optional).
            display: Whether to show the live detection feed.
        """
        if not self.fold_area_coords:
            self.setup_fold_area()
        
        if not self.is_background_initialized:
            self.initialize_background()
            
        print("Starting fold detection. Press 'q' to quit, 'r' to reset background.")
        
        while True:
            frame = self.cap.capture_array()
            if frame is None:
                print("Failed to capture frame from camera")
                break
                
            # Check for a fold event in the current frame
            fold_detected = self.detect_fold_event(frame)
            
            if display:
                # Draw the fold area on the frame
                x, y, w, h = self.fold_area_coords
                roi = frame[y:y+h, x:x+w]
                
                if self.is_background_initialized:
                    roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                    bg_gray = cv2.cvtColor(self.background, cv2.COLOR_BGR2GRAY)
                    diff = cv2.absdiff(roi_gray, bg_gray)
                    _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
                    
                    # Create a visual overlay highlighting changed areas in red
                    roi_overlay = roi.copy()
                    roi_overlay[thresh > 0] = [0, 0, 255]
                    
                    # Prepare a visualization with three panels: full frame, ROI, and ROI with overlay
                    h1, w1 = frame.shape[:2]
                    h2, w2 = roi.shape[:2]
                    vis_frame = np.zeros((h1, w1 + w2 * 2, 3), dtype=np.uint8)
                    
                    vis_frame[:h1, :w1] = frame
                    cv2.rectangle(vis_frame[:h1, :w1], (x, y), (x+w, y+h), (0, 0, 255), 2)
                    
                    vis_frame[:h2, w1:w1+w2] = roi
                    vis_frame[:h2, w1+w2:w1+w2*2] = roi_overlay
                    
                    cv2.putText(vis_frame, "Camera Feed", (10, 20),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    cv2.putText(vis_frame, "Fold Area", (w1 + 10, 20),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    cv2.putText(vis_frame, "Difference", (w1 + w2 + 10, 20),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                else:
                    vis_frame = frame.copy()
                    cv2.rectangle(vis_frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                
                # If a fold is detected, overlay text and notify game manager
                if fold_detected:
                    cv2.putText(vis_frame, "FOLD DETECTED!", (10, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    self.notify_game_state_manager(player_id)
                
                # Display instructions on the frame
                h1, _ = frame.shape[:2]
                cv2.putText(vis_frame, "Press 'q' to quit, 'r' to reset background",
                            (10, h1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                cv2.imshow("Fold Detection", vis_frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('r'):
                    print("Resetting background...")
                    self.initialize_background()
            else:
                if fold_detected:
                    self.notify_game_state_manager(player_id)
                
        # Cleanup resources
        self.cap.stop()
        if display:
            cv2.destroyAllWindows()
        print("Fold detection ended.")


def main():
    """Run the fold detector as a standalone script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Simple Poker Fold Detector for Raspberry Pi")
    parser.add_argument('--camera', type=int, default=0, help='Camera ID to use (ignored by Picamera2)')
    parser.add_argument('--player', type=int, default=None, help='Player ID being monitored')
    parser.add_argument('--area', type=str, default=None,
                        help='Fold area coordinates (x,y,w,h), comma-separated')
    parser.add_argument('--threshold', type=int, default=500, help='Detection threshold (area in pixels)')
    parser.add_argument('--cooldown', type=float, default=2.0, help='Cooldown between detections (seconds)')
    parser.add_argument('--sensitivity', type=int, default=20, help='Motion detection sensitivity (5-50)')
    
    args = parser.parse_args()
    
    # Parse fold area if provided; otherwise, interactive setup will occur.
    fold_area = None
    if args.area:
        fold_area = tuple(map(int, args.area.split(',')))
    
    detector = FoldDetector(
        camera_id=args.camera,
        fold_area_coords=fold_area,
        detection_threshold=args.threshold,
        fold_cooldown=args.cooldown,
        motion_sensitivity=args.sensitivity
    )
    
    detector.run(player_id=args.player)

if __name__ == "__main__":
    main()
