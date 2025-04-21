# 🚨 Secure-Vision: YOLOv8 Live Surveillance System

This is a real-time surveillance application built with FastAPI and YOLOv8 that captures webcam footage, detects objects, and generates PDF reports based on detection events. It's designed to be fast, lightweight, and extensible for security applications.

---

## ✅ Features

- 🎥 Live webcam feed in browser
- 🧠 YOLOv8 object detection on captured frames
- 📸 Manual snapshot capture with annotation
- 📋 Object label + confidence display
- 🧾 PDF report generation with detected objects
- 📦 Docker-ready deployment

---

## 🧪 How to Run (Locally)

```bash
# 1. Navigate to your project directory
cd yolov8_live_surveillance

# 2. (Optional) Create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install requirements
pip install -r requirements.txt

# 4. Run the app
uvicorn main:app --reload

# 5. Visit the app in your browser
http://127.0.0.1:8000/
```

---

## 🐳 How to Run with Docker

```bash
# Build the image
docker build -t secure-vision .

# Run the container
docker run -p 8000:8000 secure-vision
```

If you're on Linux and want to access your webcam in Docker:

```bash
docker run -p 8000:8000 --device=/dev/video0 secure-vision
```

---

## 📂 Project Structure

```
├── main.py               # FastAPI app with YOLOv8 logic
├── report_gen.py         # PDF report generator
├── templates/
│   └── index.html        # Frontend interface
├── static/               # Saved images + reports
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## ✨ Sample Use Cases

- Home/Office Security Monitoring
- Intruder/Object Detection in restricted zones
- Integration with smart CCTV systems

---

## 👨‍💻 Author

Built with ❤️ by Taksheel Singh Rawat

