from __future__ import annotations

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR.parent
PROJECT_DIR = BACKEND_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
APP_DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"
SNAPSHOT_DIR = BASE_DIR / "snapshots"

VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}
EXCLUDED_VIDEO_FILENAMES = set()
SUPPORTED_CLASSES = ["car", "motorcycle", "bus", "truck", "person"]
VEHICLE_CLASSES = ["car", "motorcycle", "bus", "truck"]

FRAME_WIDTH = 960
FRAME_SKIP = 5
OCR_INTERVAL = 20
CONFIDENCE_THRESHOLD = 0.35
PLATE_MIN_CONFIDENCE = 0.55
HIGH_DENSITY_THRESHOLD = 12
MULTI_CHALLAN_ALERT_THRESHOLD = 3
STREAM_JPEG_QUALITY = 72

APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
