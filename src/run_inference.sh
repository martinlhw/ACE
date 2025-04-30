import os
# Configure Qt platform: use on-screen if DISPLAY is defined, otherwise offscreen
if os.environ.get("DISPLAY"):
    # clear any offscreen override
    os.environ.pop("QT_QPA_PLATFORM", None)
else:
    os.environ["QT_QPA_PLATFORM"] = "offscreen"

import cv2
import torch
import time
import argparse
from PIL import Image
import torchvision.transforms as transforms
import sys
from picamera2 import Picamera2

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from train.model import PokerCardClassifier

# ─────────────────────────── model loader ──────────────────────────

def load_model(checkpoint_path: str, num_classes: int, device: str = "cpu"):
    """Load `PokerCardClassifier` weights from checkpoint"""
    model = PokerCardClassifier(num_classes)
    ckpt = torch.load(checkpoint_path, map_location=device)
    state = ckpt.get("model_state_dict", ckpt)
    model.load_state_dict(state)
    return model.to(device)


# ──────────────────────────── detector class ──────────────────────
class RealtimeCardDetector:
    """Grab frames via Picamera2, classify, and finalise when stable."""

    def __init__(
        self,
        model_path: str,
        class_names: list[str],
        device: str = "cpu",
        input_size: tuple[int, int] = (224, 224),
        conf_threshold: float = 0.7,
        fps_avg_frames: int = 10,
    ) -> None:
        self.device = device
        self.class_names = class_names
        self.conf_display = conf_threshold * 100

        # load and eval model
        self.model = load_model(model_path, len(class_names), device)
        self.model.eval()

        # preprocessing transform
        self.transform = transforms.Compose([
            transforms.Resize(input_size),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225])
        ])

        # fps tracking
        self.fps_times: list[float] = []
        self.fps_avg = fps_avg_frames

        # finalisation state
        self.finalised = False
        self.final_class: str | None = None
        self.candidate_class: str | None = None
        self.t70_start: float | None = None
        self.t90_start: float | None = None

        # initialize camera
        self.picam = Picamera2()
        self.picam.configure(
            self.picam.create_preview_configuration(
                main={"size": (640, 480), "format": "BGR888"}
            )
        )
        self.picam.start()
        print("Detector ready – press q to quit.")

    # ───────────────────────── internal helpers ────────────────────
    def _preprocess(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil = Image.fromarray(rgb)
        return self.transform(pil).unsqueeze(0).to(self.device)

    @torch.no_grad()
    def _predict(self, frame):
        tensor = self._preprocess(frame)
        probs = torch.nn.functional.softmax(self.model(tensor), dim=1)
        conf, pred = torch.max(probs, 1)
        return self.class_names[pred.item()], conf.item() * 100

    def _update_fps(self):
        now = time.time()
        self.fps_times.append(now)
        if len(self.fps_times) > self.fps_avg:
            self.fps_times.pop(0)
        if len(self.fps_times) > 1:
            dt = self.fps_times[-1] - self.fps_times[0]
            if dt > 0:
                return (len(self.fps_times) - 1) / dt
        return 0.0

    # ─────────────────────── finalisation logic ────────────────────
    def _track_stability(self, cls: str, conf: float):
        now = time.time()
        if cls != self.candidate_class:
            self.candidate_class = cls
            self.t70_start = now if conf >= 70 else None
            self.t90_start = now if conf >= 90 else None
            return
        if conf >= 90:
            self.t90_start = self.t90_start or now
            if now - self.t90_start >= 1:
                self._finalise(cls)
        else:
            self.t90_start = None
        if conf >= 70:
            self.t70_start = self.t70_start or now
            if now - self.t70_start >= 2:
                self._finalise(cls)
        else:
            self.t70_start = None

    def _finalise(self, cls: str):
        self.finalised = True
        self.final_class = cls
        print(f"✔ Final prediction: {cls}")

    # ───────────────────────────── main loop ──────────────────────
    def run(self, display_scale: float = 1.0):
        # determine if we have a real GUI
        gui = bool(os.environ.get("DISPLAY")) and os.environ.get("QT_QPA_PLATFORM") != "offscreen"
        if gui:
            print(f"[DEBUG] GUI ON, DISPLAY={os.environ.get('DISPLAY')}")
            cv2.startWindowThread()
            cv2.namedWindow("Poker Card Detection", cv2.WINDOW_NORMAL)
            cv2.setWindowProperty(
                "Poker Card Detection",
                cv2.WND_PROP_FULLSCREEN,
                cv2.WINDOW_FULLSCREEN
            )
        else:
            print("[DEBUG] head-less mode")

        try:
            while True:
                frame = self.picam.capture_array()
                if not self.finalised:
                    cls, conf = self._predict(frame)
                    self._track_stability(cls, conf)
                else:
                    cls, conf = self.final_class, 100.0

                fps = self._update_fps()
                disp = frame.copy()

                # overlay text
                if self.finalised:
                    cv2.putText(disp, f"FINAL: {cls}", (10, 40),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                                (0, 255, 255), 3)
                else:
                    if conf >= self.conf_display:
                        cv2.putText(disp, f"Card: {cls}", (10, 30),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.9,
                                    (0, 255, 0), 2)
                        cv2.putText(disp, f"Conf: {conf:.1f}%", (10, 70),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.9,
                                    (0, 255, 0), 2)
                    else:
                        cv2.putText(disp, "No card detected", (10, 30),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.9,
                                    (0, 0, 255), 2)
                cv2.putText(disp, f"FPS: {fps:.1f}", (10, 110),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                            (255, 0, 0), 2)

                # resize if requested
                if display_scale != 1.0:
                    w = int(disp.shape[1] * display_scale)
                    h = int(disp.shape[0] * display_scale)
                    disp = cv2.resize(disp, (w, h))

                # show window if GUI
                if gui:
                    cv2.imshow("Poker Card Detection", disp)
                # handle key or sleep
                key = cv2.waitKey(1) & 0xFF if gui else None
                if key == ord("q"):
                    break

        except KeyboardInterrupt:
            pass
        finally:
            self.picam.stop()
            if gui:
                cv2.destroyAllWindows()
            print("Detection ended")

# ─────────────────────────────── CLI ──────────────────────────────

def load_class_names(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    return [l.strip() for l in open(path) if l.strip()]

def main():
    ap = argparse.ArgumentParser("Real-time Poker Card Detector (Picamera2)")
    ap.add_argument("--model", required=True)
    ap.add_argument("--classes", required=True)
    ap.add_argument("--threshold", type=float, default=0.7)
    ap.add_argument("--display_scale", type=float, default=1.0)
    ap.add_argument("--device", default="cpu")
    args = ap.parse_args()
    detector = RealtimeCardDetector(
        model_path=args.model,
        class_names=load_class_names(args.classes),
        device=args.device,
        conf_threshold=args.threshold,
    )
    detector.run(display_scale=args.display_scale)

if __name__ == "__main__":
    main()
