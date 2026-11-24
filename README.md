# 🚨 Secure-Vision: YOLOv8 Live Surveillance & Automated Audit System

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-00599C?logo=yolo&logoColor=white)](https://docs.ultralytics.com/)
[![Design](https://img.shields.io/badge/Theme-Rosé%20Pine%20Dawn-575279)](https://rosepinetheme.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)

**Secure-Vision** is a production-hardened, real-time computer vision surveillance microservice. Built with **FastAPI**, **YOLOv8**, and **FPDF2**, it delivers throttled MJPEG video streaming, thread-safe on-demand object detection, dynamic confidence thresholding, and automated visual PDF audit reporting.

Styled using the **Rosé Pine Dawn** design system (shadcn/ui aesthetic) with **Geist** typography, Secure-Vision operates seamlessly across physical hardware or headless/containerized environments.

---

## ✨ Key Features

* 🎥 **Thread-Safe Live Streaming:** Decoupled producer-consumer camera pipeline streaming MJPEG at a stable ~25 FPS without thread contention or CPU pinning.
* 🧪 **Zero-Hardware Simulation Fallback:** Automatically detects physical webcam availability. If running in a headless VM, container, or cloud without a camera, it generates a dynamic synthetic CCTV test card with animated timestamps and optical crosshairs so the server **never crashes**.
* 🎛️ **Active Confidence Threshold Slider:** Interactively adjust detection confidence (10% to 90%) directly from the UI. YOLOv8 actively filters out low-confidence predictions before saving frames or generating reports.
* ⚡ **True Latency Measurement:** Measures genuine client-to-server round-trip latency in milliseconds (`performance.now()`), showing exact network transit + PyTorch inference time on every snapshot.
* 🧾 **Visual PDF Surveillance Reports:** Compiles high-resolution, annotated snapshot images directly into downloadable audit documents alongside timestamps, detection labels, and confidence ratings.
* 🎨 **Rosé Pine Dawn Interface:** Single-page dashboard built with Geist Sans, Geist Mono (`tabular-nums`), and 100vh viewport-locked split-pane layout with zero page scroll.
* 🛡️ **Enterprise Security & Defense:**
  * **Path Traversal Defense:** Strict regex sanitization (`^[a-zA-Z0-9_-]{1,64}$`) on session IDs, blocking malicious directory traversal attempts (`../../etc/passwd`) with HTTP 400.
  * **Security Headers Middleware:** Enforces `Content-Security-Policy` (CSP), `X-Frame-Options: SAMEORIGIN`, `X-Content-Type-Options: nosniff`, and `Referrer-Policy`.
  * **Automated Disk & Inode Protection:** Bounded file retention automatically prunes old snapshots (max 50 images) and PDF reports (max 10 documents) to prevent disk exhaustion.
* ⌨️ **Tactical Keyboard Shortcuts:**
  * <kbd>Space</kbd> — Trigger instant snapshot capture and YOLO detection.
  * <kbd>R</kbd> — Compile and download PDF audit report.
  * <kbd>F</kbd> — Toggle full-viewport video feed.

---

## 📂 Project Structure

```text
Secure-Vision/
├── main.py               # FastAPI backend (CameraService, YOLO pipeline, routes, security)
├── report_gen.py         # Visual PDF generator (fpdf2, custom header/footer, photo embedding)
├── templates/
│   └── index.html        # Rosé Pine Dawn C2 frontend dashboard
├── static/               # Bounded snapshot frames and generated PDF reports
├── test_e2e.py           # Automated end-to-end regression & security test suite
├── Dockerfile            # Container deployment configuration
├── requirements.txt      # Pinned dependency manifest
├── .gitignore            # Git exclusion rules
├── .dockerignore          # Container build context filter
└── README.md
```

---

## 🧪 Quickstart (Run Locally)

### 1. Clone the repository
```bash
git clone https://github.com/TaksheelSingh/Secure-Vision
cd Secure-Vision
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Start the application
```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### 5. Access the dashboard
Open your browser and navigate to:
```text
http://127.0.0.1:8000/
```

---

## 🐳 Run with Docker

Build and run Secure-Vision inside an isolated container:

```bash
# Build the Docker image
docker build -t secure-vision .

# Run container (Simulation Mode)
docker run -p 8000:8000 secure-vision
```

If you are on Linux and wish to pass through a physical webcam:
```bash
docker run -p 8000:8000 --device=/dev/video0 secure-vision
```

---

## 🧪 Automated Testing & Verification

Secure-Vision includes a comprehensive automated test suite validating security headers, path traversal protection, MJPEG streaming, YOLO inference, and PDF compilation:

```bash
python test_e2e.py
```

Expected output:
```text
>>> 1. Initializing TestClient and Lifespan...
>>> Lifespan started successfully.
>>> 2. Testing GET / (Home Page & Security Headers)...
   [PASS] Home page & security headers verified.
>>> 3. Testing GET /video_feed (Streaming MJPEG)...
   [PASS] Video streaming active.
>>> 4. Testing Path Traversal Defense on /capture...
   [PASS] Malicious session_id correctly rejected with HTTP 400.
>>> 5. Testing POST /capture (Valid YOLO Detection)...
   [PASS] Capture succeeded.
>>> 6. Testing Path Traversal Defense on /generate_report...
   [PASS] Malicious report request correctly rejected with HTTP 400.
>>> 7. Testing GET /generate_report (Visual PDF Generation)...
   [PASS] PDF generated successfully.

>>> ALL PIPELINE & SECURITY REGRESSION CHECKS PASSED! <<<
```

---

## 👨‍💻 Author

Built with ❤️ by **Taksheel Singh Rawat**
