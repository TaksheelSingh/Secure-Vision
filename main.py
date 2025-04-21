import os
import uuid
import cv2
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from ultralytics import YOLO
from report_gen import generate_pdf_report

# Initialize FastAPI app
app = FastAPI()

# Load YOLOv8 model
model = YOLO("yolov8n.pt")  # You can switch to 'yolov8s.pt' or others

# Initialize camera
cap = cv2.VideoCapture(0)

# Paths
STATIC_DIR = "static"
os.makedirs(STATIC_DIR, exist_ok=True)

# Mount static and templates
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory="templates")

# Store events for report
event_log = []

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

def generate_frames():
    while True:
        success, frame = cap.read()
        if not success:
            break
        _, buffer = cv2.imencode('.jpg', frame)
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")

@app.get("/video_feed")
def video_feed():
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.post("/capture")
def capture():
    success, frame = cap.read()
    if not success:
        return JSONResponse({"error": "Failed to capture from webcam."}, status_code=500)

    results = model.predict(source=frame, conf=0.25, save=False, verbose=False)
    boxes = results[0].boxes
    annotated = results[0].plot()

    # Save annotated image
    filename = f"frame_{uuid.uuid4().hex}.jpg"
    filepath = os.path.join(STATIC_DIR, filename)
    cv2.imwrite(filepath, annotated)

    # Extract detection results
    snapshot_events = []
    for box in boxes:
        label = model.names[int(box.cls.item())]
        conf = round(box.conf.item(), 2)
        snapshot_events.append({
            "frame": filename,
            "label": label,
            "confidence": conf,
            "image": f"/static/{filename}"
        })

    # Log for report
    event_log.extend(snapshot_events)

    return {
        "image_url": f"/static/{filename}",
        "events": snapshot_events
    }

@app.get("/generate_report")
def generate_report():
    report_path = os.path.join(STATIC_DIR, "surveillance_report.pdf")
    generate_pdf_report(event_log, report_path)
    return FileResponse(report_path, media_type="application/pdf", filename="surveillance_report.pdf")
