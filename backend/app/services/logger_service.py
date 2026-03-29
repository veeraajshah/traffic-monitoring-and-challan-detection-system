from __future__ import annotations

import csv
import json
from pathlib import Path
from threading import Lock
from typing import Any

from app.config import LOG_DIR


class DetectionLogger:
    def __init__(self) -> None:
        self.csv_path = LOG_DIR / "detections.csv"
        self.json_path = LOG_DIR / "detections.json"
        self._lock = Lock()
        self._fieldnames = [
            "timestamp",
            "source_id",
            "object_id",
            "object_type",
            "confidence",
            "license_plate",
            "challan_status",
            "fine_amount",
            "violation_type",
        ]
        self._ensure_headers()

    def _ensure_headers(self) -> None:
        if self.csv_path.exists():
            return
        with self.csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=self._fieldnames)
            writer.writeheader()

    def log(self, row: dict[str, Any]) -> None:
        with self._lock:
            with self.csv_path.open("a", newline="", encoding="utf-8") as csv_handle:
                writer = csv.DictWriter(csv_handle, fieldnames=self._fieldnames)
                writer.writerow(row)
            with self.json_path.open("a", encoding="utf-8") as json_handle:
                json_handle.write(json.dumps(row) + "\n")
