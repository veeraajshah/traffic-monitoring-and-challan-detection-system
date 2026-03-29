# Real-Time Traffic Monitoring and Challan Detection

Production-style full-stack demo for traffic video monitoring using the four local CCTV videos inside [`/Users/veeraajshah/Desktop/projects /ivp project/data`](/Users/veeraajshah/Desktop/projects%20/ivp%20project/data).

## What it includes

- FastAPI backend for source discovery, MJPEG video streaming, metadata polling, challan lookup, snapshot capture, and CSV/JSON logging
- React + Tailwind dashboard for live feed viewing, source switching, vehicle filtering, real-time metrics, alerts, and challan cards
- Pluggable inference pipeline:
  - Uses `YOLOv8` and `EasyOCR` when available
  - Falls back to a heuristic detection path so the app still runs for UI/demo purposes if model setup is incomplete
- Built-in mock challan database with automatic lookup at plate-detection time

## Video sources

The backend auto-loads every supported video file from [`/Users/veeraajshah/Desktop/projects /ivp project/data`](/Users/veeraajshah/Desktop/projects%20/ivp%20project/data):

- `Traffic Control CCTV.mp4`
- `pexels-george-morina-5222550 (2160p).mp4`
- `pexels-christopher-schultz-5927708 (1080p).mp4`
- `pexels-casey-whalen-6571483 (2160p).mp4`

## Backend setup

```bash
cd "/Users/veeraajshah/Desktop/projects /ivp project/backend"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend base URL: [http://127.0.0.1:8000](http://127.0.0.1:8000)

Useful endpoints:

- `GET /get_videos`
- `POST /set_video`
- `GET /video_feed?source_id=<id>`
- `GET /metadata?source_id=<id>&vehicle_type=car`
- `GET /check_challan/<plate>`
- `GET /export_logs?format=csv`
- `GET /snapshots`

## Frontend setup

```bash
cd "/Users/veeraajshah/Desktop/projects /ivp project/frontend"
npm install
npm run dev
```

Frontend dev URL: [http://127.0.0.1:5173](http://127.0.0.1:5173)

If your backend runs on another host or port, set:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## Notes on AI inference

- `ultralytics` will download YOLO weights on first run if they are not already cached.
- `easyocr` may also fetch model assets the first time it is initialized.
- If those downloads are unavailable, the backend stays operational using the fallback path, which keeps the dashboard, logging, filtering, alerts, and challan flow demoable.

## Generated artifacts

- Logs:
  - [`/Users/veeraajshah/Desktop/projects /ivp project/backend/app/logs/detections.csv`](/Users/veeraajshah/Desktop/projects%20/ivp%20project/backend/app/logs/detections.csv)
  - [`/Users/veeraajshah/Desktop/projects /ivp project/backend/app/logs/detections.json`](/Users/veeraajshah/Desktop/projects%20/ivp%20project/backend/app/logs/detections.json)
- Snapshots:
  - [`/Users/veeraajshah/Desktop/projects /ivp project/backend/app/snapshots`](/Users/veeraajshah/Desktop/projects%20/ivp%20project/backend/app/snapshots)

## Suggested next step

For a stronger production path, add a dedicated license-plate detector before OCR and move the challan store from JSON to MongoDB or PostgreSQL.
