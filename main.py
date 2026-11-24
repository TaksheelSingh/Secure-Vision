import os
import re
import time
import uuid
import threading
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional

import cv2
import numpy as np
from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.concurrency import run_in_threadpool
from ultralytics import YOLO

from report_gen import generate_pdf_report

STATIC_DIR = "static"
os.makedirs(STATIC_DIR, exist_ok=True)

# Strict session identifier pattern to prevent path traversal (e.g. '../')
SESSION_ID_REGEX = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")

def validate_session_id(session_id: str) -> str:
    """Validates session identifier against directory traversal and invalid characters."""
    if not SESSION_ID_REGEX.match(session_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid session identifier format. Only alphanumeric characters, dashes, and underscores allowed (max 64 chars)."
        )
    return session_id

class CameraService:
    """Thread-safe camera service with background capture and synthetic fallback."""
    def __init__(self, camera_index: int = 0):
        self.camera_index = camera_index
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_running = False
        self.camera_available = False
        self.current_frame: Optional[np.ndarray] = None
        self.lock = threading.Lock()
        self.thread: Optional[threading.Thread] = None

    def start(self):
        self.cap = cv2.VideoCapture(self.camera_index)
        if self.cap.isOpened():
            success, test_frame = self.cap.read()
            if success and test_frame is not None:
                self.camera_available = True
                with self.lock:
                    self.current_frame = test_frame
            else:
                self.camera_available = False
        else:
            self.camera_available = False

        self.is_running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()

    def _generate_synthetic_frame(self) -> np.ndarray:
        """Generates a dynamic CCTV test card if no hardware webcam is detected."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[:] = (35, 25, 20)
        cv2.rectangle(frame, (10, 10), (630, 470), (0, 200, 255), 2)
        cv2.putText(frame, "SECURE-VISION CCTV FEED [SIMULATION]", (30, 45),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        status_text = "HARDWARE WEBCAM OFFLINE - DEMO MODE"
        cv2.putText(frame, status_text, (30, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 255), 1)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        cv2.putText(frame, f"REC: {now_str}", (30, 450),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.line(frame, (320, 220), (320, 260), (0, 200, 255), 1)
        cv2.line(frame, (300, 240), (340, 240), (0, 200, 255), 1)
        return frame

    def _capture_loop(self):
        while self.is_running:
            if self.camera_available and self.cap is not None:
                success, frame = self.cap.read()
                if success and frame is not None:
                    with self.lock:
                        self.current_frame = frame
                else:
                    self.camera_available = False
            else:
                synth = self._generate_synthetic_frame()
                with self.lock:
                    self.current_frame = synth
            time.sleep(0.033)  # ~30 FPS

    def get_latest_frame(self) -> Optional[np.ndarray]:
        with self.lock:
            if self.current_frame is not None:
                return self.current_frame.copy()
        return None

    def stop(self):
        self.is_running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        if self.cap is not None:
            self.cap.release()
            self.cap = None

camera_service = CameraService()
yolo_model: Optional[YOLO] = None
yolo_lock = threading.Lock()

session_event_logs: dict[str, list] = {}
session_lock = threading.Lock()

def cleanup_old_static_files(max_images: int = 50, max_pdfs: int = 10):
    """Prunes old frames and reports to prevent disk and inode exhaustion."""
    try:
        # Prune JPEG snapshots
        img_files = [
            os.path.join(STATIC_DIR, f)
            for f in os.listdir(STATIC_DIR)
            if f.startswith("frame_") and f.endswith(".jpg")
        ]
        if len(img_files) > max_images:
            img_files.sort(key=os.path.getmtime)
            for f in img_files[:-max_images]:
                try:
                    os.remove(f)
                except OSError:
                    pass

        # Prune generated PDF reports
        pdf_files = [
            os.path.join(STATIC_DIR, f)
            for f in os.listdir(STATIC_DIR)
            if f.startswith("surveillance_report_") and f.endswith(".pdf")
        ]
        if len(pdf_files) > max_pdfs:
            pdf_files.sort(key=os.path.getmtime)
            for f in pdf_files[:-max_pdfs]:
                try:
                    os.remove(f)
                except OSError:
                    pass
    except Exception:
        pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    global yolo_model
    yolo_model = YOLO("yolov8n.pt")
    camera_service.start()
    yield
    camera_service.stop()

app = FastAPI(title="Secure-Vision", lifespan=lifespan)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "img-src 'self' data: blob:; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "script-src 'self' 'unsafe-inline'; "
        "connect-src 'self'"
    )
    return response

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

async def generate_frames_stream():
    """Streams JPEG frames with throttled frame rate to prevent CPU pinning."""
    while True:
        frame = camera_service.get_latest_frame()
        if frame is None:
            await asyncio.sleep(0.04)
            continue
        success, buffer = cv2.imencode('.jpg', frame)
        if not success:
            await asyncio.sleep(0.04)
            continue
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")
        await asyncio.sleep(0.04)  # ~25 FPS

@app.get("/video_feed")
def video_feed():
    return StreamingResponse(
        generate_frames_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

def _predict_and_annotate(frame: np.ndarray, conf: float = 0.25):
    with yolo_lock:
        results = yolo_model.predict(source=frame, conf=conf, save=False, verbose=False)
        boxes = results[0].boxes
        annotated = results[0].plot()
        names = yolo_model.names
    return boxes, annotated, names

@app.post("/capture")
async def capture(session_id: str = Query(default="default"), conf: float = Query(default=0.25)):
    clean_session = validate_session_id(session_id)
    conf_threshold = max(0.05, min(0.95, conf))

    frame = camera_service.get_latest_frame()
    if frame is None:
        return JSONResponse({"error": "Camera frame unavailable."}, status_code=500)

    # Run YOLO in background threadpool to avoid blocking event loop
    boxes, annotated, names = await run_in_threadpool(_predict_and_annotate, frame, conf_threshold)

    # Save annotated snapshot
    filename = f"frame_{uuid.uuid4().hex}.jpg"
    filepath = os.path.join(STATIC_DIR, filename)
    cv2.imwrite(filepath, annotated)

    # Prune old images and reports
    cleanup_old_static_files(max_images=50, max_pdfs=10)

    now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    snapshot_events = []
    for box in boxes:
        label = names[int(box.cls.item())]
        confidence = round(box.conf.item(), 2)
        snapshot_events.append({
            "frame": filename,
            "filepath": filepath,
            "label": label,
            "confidence": confidence,
            "image": f"/static/{filename}",
            "timestamp": now_iso
        })

    # Record in session-isolated store
    with session_lock:
        if clean_session not in session_event_logs:
            session_event_logs[clean_session] = []
        session_event_logs[clean_session].extend(snapshot_events)
        if len(session_event_logs[clean_session]) > 100:
            session_event_logs[clean_session] = session_event_logs[clean_session][-100:]

    return {
        "image_url": f"/static/{filename}",
        "events": snapshot_events,
        "is_camera_hardware": camera_service.camera_available,
        "total_logged": len(session_event_logs.get(clean_session, []))
    }

@app.get("/generate_report")
async def generate_report(session_id: str = Query(default="default")):
    clean_session = validate_session_id(session_id)

    with session_lock:
        events = list(session_event_logs.get(clean_session, []))

    # Generate unique report filename per request to prevent concurrency collisions
    report_filename = f"surveillance_report_{clean_session}_{uuid.uuid4().hex[:8]}.pdf"
    report_path = os.path.join(STATIC_DIR, report_filename)

    await run_in_threadpool(generate_pdf_report, events, report_path)

    if not os.path.exists(report_path):
        raise HTTPException(status_code=500, detail="Failed to generate PDF report.")

    # Periodic cleanup of old static reports
    cleanup_old_static_files(max_images=50, max_pdfs=10)

    return FileResponse(
        report_path,
        media_type="application/pdf",
        filename=f"surveillance_report_{clean_session}.pdf"
    )
