import cv2
import torch
import time
import argparse
import os
import socket
import json
os.environ["QT_QPA_PLATFORM"] = "xcb"
os.environ["GDK_BACKEND"] = "x11"
os.environ["OPENCV_VIDEOIO_PRIORITY_BACKEND"] = "gstreamer"

from PIL import Image
import torchvision.transforms as transforms
import sys
from picamera2 import Picamera2

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from train.model import PokerCardClassifier

# ─────────────────────────── model loader ──────────────────────────

def load_model(checkpoint_path: str, num_classes: int, device: str = "cpu"):
    """Load PokerCardClassifier weights from checkpoint"""
    model = PokerCardClassifier(num_classes)
    ckpt = torch.load(checkpoint_path, map_location=device)
    state = ckpt.get("model_state_dict", ckpt)
    model.load_state_dict(state)
    return model.to(device)


# ──────────────────────────── detector class ──────────────────────
class RealtimeCardDetector:
    """Realtime poker card detector using Picamera2 and OpenCV GUI."""

    def __init__(
        self,
        model_path: str,
        class_names: list[str],
        device: str = "cpu",
        input_size: tuple[int, int] = (224, 224),
        conf_threshold: float = 0.7,
        fps_avg_frames: int = 10,
        socket_host="localhost",
        socket_port=12345
    ) -> None:
        self.device = device
        self.class_names = class_names
        self.conf_threshold = conf_threshold * 100

        # Load and prepare model
        self.model = load_model(model_path, len(class_names), device)
        self.model.eval()

        # Preprocessing pipeline
        self.transform = transforms.Compose([
            transforms.Resize(input_size),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

        # FPS tracking
        self.fps_times: list[float] = []
        self.fps_avg = fps_avg_frames

        # Finalisation state
        self.finalised = False
        self.final_class: str | None = None
        self.candidate_class: str | None = None
        self.t70_start: float | None = None
        self.t90_start: float | None = None
        
        # Socket connection for transmitting results
        self.socket_host = socket_host
        self.socket_port = socket_port
        self.socket = None
        self.connect_socket()

        # Initialize camera
        self.picam = Picamera2()
        self.picam.configure(
            self.picam.create_preview_configuration(
                main={"size": (640, 480), "format": "BGR888"}
            )
        )
        self.picam.start()
        print("Detector ready – press q in the window to quit.")
    
    def connect_socket(self):
        """Establish socket connection to the game state manager"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.socket_host, self.socket_port))
            print(f"Connected to game state manager at {self.socket_host}:{self.socket_port}")
        except Exception as e:
            print(f"Failed to connect to game state manager: {e}")
            self.socket = None

    def _preprocess(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil = Image.fromarray(rgb)
        return self.transform(pil).unsqueeze(0).to(self.device)

    @torch.no_grad()
    def _predict(self, frame):
        tensor = self._preprocess(frame)
        outputs = self.model(tensor)
        probs = torch.nn.functional.softmax(outputs, dim=1)
        conf, idx = torch.max(probs, 1)
        return self.class_names[idx.item()], conf.item() * 100

    def _update_fps(self):
        now = time.time()
        self.fps_times.append(now)
        if len(self.fps_times) > self.fps_avg:
            self.fps_times.pop(0)
        if len(self.fps_times) > 1:
            dt = self.fps_times[-1] - self.fps_times[0]
            return (len(self.fps_times) - 1) / dt if dt > 0 else 0.0
        return 0.0

    def _track_stability(self, cls: str, conf: float):
        now = time.time()
        
        # Reset finalization if a different card is detected with good confidence
        if self.finalised and cls != self.final_class and conf >= self.conf_threshold:
            print(f"New card detected: {cls}, confidence: {conf:.1f}%")
            self.finalised = False
            self.final_class = None
            self.candidate_class = cls
            self.t70_start = now if conf >= 70 else None
            self.t90_start = now if conf >= 90 else None
            return
            
        # If not finalized yet, track stability as before
        if cls != self.candidate_class:
            self.candidate_class = cls
            self.t80_start = now if conf >= 80 else None
            self.t90_start = now if conf >= 90 else None
            return
            
        if conf >= 90:
            if self.t90_start is None:
                self.t90_start = now
            elif now - self.t90_start >= 1:
                self._finalise(cls)
        else:
            self.t90_start = None
            
        if conf >= 80:
            if self.t80_start is None:
                self.t80_start = now
            elif now - self.t80_start >= 2:
                self._finalise(cls)
        else:
            self.t80_start = None

    def _finalise(self, cls: str):
        self.finalised = True
        self.final_class = cls
        print(f"✔ Final prediction: {cls}")
        
        # Send the detection to the game state manager
        if self.socket:
            try:
                # Simply send the card class as a string
                self.socket.sendall(cls.encode('utf-8'))
                print(f"Sent detection '{cls}' to game state manager")
            except Exception as e:
                print(f"Failed to send detection: {e}")
                # Try to reconnect on failure
                self.connect_socket()
        
    def _send_detection(self, card_class: str):
        """Send detection result to the game state manager"""
        if self.socket:
            try:
                # Create a message with the card data
                message = {
                    "type": "card_detection",
                    "card": card_class,
                    "timestamp": time.time()
                }
                
                # Convert to JSON and send
                json_message = json.dumps(message) + "\n"  # Add newline as message delimiter
                self.socket.sendall(json_message.encode('utf-8'))
                print(f"Sent detection '{card_class}' to game state manager")
            except Exception as e:
                print(f"Failed to send detection: {e}")
                # Try to reconnect on failure
                self.connect_socket()

    def run(self, display_scale: float = 1.0):
        # Create and configure window
        cv2.namedWindow("Poker Card Detection", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Poker Card Detection", 640, 480)
        cv2.moveWindow("Poker Card Detection", 100, 100)
        time.sleep(2)  # Give the window system time to initialize
        
        try:
            while True:
                frame = self.picam.capture_array()
                
                # Always predict and track stability - don't skip when finalized
                cls, conf = self._predict(frame)
                self._track_stability(cls, conf)
                
                # For display purposes, if finalized, use the final_class
                display_cls = self.final_class if self.finalised else cls
                display_conf = 100.0 if self.finalised else conf
                
                fps = self._update_fps()
                disp = frame.copy()

                # Overlay text
                if self.finalised:
                    cv2.putText(disp, f"FINAL: {display_cls}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 3)
                else:
                    if conf >= self.conf_threshold:
                        cv2.putText(disp, f"Card: {display_cls}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                        cv2.putText(disp, f"Conf: {display_conf:.1f}%", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                    else:
                        cv2.putText(disp, "No card detected", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                cv2.putText(disp, f"FPS: {fps:.1f}", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

                if display_scale != 1.0:
                    disp = cv2.resize(
                        disp,
                        (int(disp.shape[1] * display_scale), int(disp.shape[0] * display_scale)),
                    )

                # Show and handle key
                cv2.imshow("Poker Card Detection", disp)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        except KeyboardInterrupt:
            pass
        finally:
            if self.socket:
                self.socket.close()
            self.picam.stop()
            cv2.destroyAllWindows()
            print("Detection ended")


def load_class_names(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    return [l.strip() for l in open(path) if l.strip()]


def main():
    parser = argparse.ArgumentParser("Real-time Poker Card Detector (Picamera2)")
    parser.add_argument("--model", required=True)
    parser.add_argument("--classes", required=True)
    parser.add_argument("--threshold", type=float, default=0.8)
    parser.add_argument("--display_scale", type=float, default=1.0)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=12345)
    args = parser.parse_args()

    detector = RealtimeCardDetector(
        model_path=args.model,
        class_names=load_class_names(args.classes),
        device=args.device,
        conf_threshold=args.threshold,
        socket_host=args.host,
        socket_port=args.port
    )
    detector.run(display_scale=args.display_scale)


if __name__ == "__main__":
    main()