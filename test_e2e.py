import os
import sys
from fastapi.testclient import TestClient
from main import app

def test_full_pipeline():
    print(">>> 1. Initializing TestClient and Lifespan...")
    with TestClient(app) as client:
        print(">>> Lifespan started successfully.")

        # Test GET / & Security Headers
        print(">>> 2. Testing GET / (Home Page & Security Headers)...")
        res = client.get("/")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        assert "Secure-Vision" in res.text
        assert res.headers.get("x-frame-options") == "SAMEORIGIN", "Missing X-Frame-Options header"
        assert res.headers.get("x-content-type-options") == "nosniff", "Missing nosniff header"
        assert "Content-Security-Policy" in res.headers or "content-security-policy" in res.headers, "Missing CSP header"
        print("   [PASS] Home page & security headers verified.")

        # Test GET /video_feed (read first chunk)
        print(">>> 3. Testing GET /video_feed (Streaming MJPEG)...")
        with client.stream("GET", "/video_feed") as stream_res:
            assert stream_res.status_code == 200
            chunk = next(stream_res.iter_bytes())
            assert b"--frame" in chunk or b"Content-Type" in chunk or len(chunk) > 0
        print("   [PASS] Video streaming active.")

        # Test Path Traversal Defense on /capture
        print(">>> 4. Testing Path Traversal Defense on /capture...")
        malicious_res = client.post("/capture?session_id=../../etc/passwd")
        assert malicious_res.status_code == 400, f"Expected 400 for path traversal, got {malicious_res.status_code}"
        print("   [PASS] Malicious session_id correctly rejected with HTTP 400.")

        # Test POST /capture with valid session_id and conf
        print(">>> 5. Testing POST /capture (Valid YOLO Detection)...")
        cap_res = client.post("/capture?session_id=unit_test_session&conf=0.25")
        assert cap_res.status_code == 200, f"Expected 200, got {cap_res.status_code}: {cap_res.text}"
        data = cap_res.json()
        assert "image_url" in data
        assert "events" in data
        assert "is_camera_hardware" in data
        print(f"   [PASS] Capture succeeded. Image URL: {data['image_url']}, Detections: {len(data['events'])}")

        # Test Path Traversal Defense on /generate_report
        print(">>> 6. Testing Path Traversal Defense on /generate_report...")
        malicious_rep = client.get("/generate_report?session_id=../..evil")
        assert malicious_rep.status_code == 400, f"Expected 400 for report path traversal, got {malicious_rep.status_code}"
        print("   [PASS] Malicious report request correctly rejected with HTTP 400.")

        # Test GET /generate_report with valid session
        print(">>> 7. Testing GET /generate_report (Visual PDF Generation)...")
        rep_res = client.get("/generate_report?session_id=unit_test_session")
        assert rep_res.status_code == 200, f"Expected 200, got {rep_res.status_code}"
        assert rep_res.headers.get("content-type") == "application/pdf"
        assert len(rep_res.content) > 1000, "PDF content seems too small"
        print(f"   [PASS] PDF generated successfully. File size: {len(rep_res.content)} bytes.")

    print("\n>>> ALL PIPELINE & SECURITY REGRESSION CHECKS PASSED! <<<")

if __name__ == "__main__":
    test_full_pipeline()
