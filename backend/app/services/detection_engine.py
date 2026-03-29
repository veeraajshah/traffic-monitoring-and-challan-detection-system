from __future__ import annotations

import re
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from threading import Event, Lock, Thread
from typing import Any

import cv2
import numpy as np

from app.config import (
    CONFIDENCE_THRESHOLD,
    FRAME_SKIP,
    FRAME_WIDTH,
    HIGH_DENSITY_THRESHOLD,
    MULTI_CHALLAN_ALERT_THRESHOLD,
    OCR_INTERVAL,
    PLATE_MIN_CONFIDENCE,
    SNAPSHOT_DIR,
    STREAM_JPEG_QUALITY,
    SUPPORTED_CLASSES,
    VEHICLE_CLASSES,
)
from app.models import ChallanRecord, VideoSource
from app.services.challan_service import ChallanService
from app.services.logger_service import DetectionLogger

PLATE_REGEX = re.compile(r"^[A-Z]{2}\d{2}[A-Z]{2}\d{4}$")
COCO_CLASS_MAP = {
    0: "person",
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}


class DetectorAdapter:
    def __init__(self, challan_service: ChallanService) -> None:
        self.challan_service = challan_service
        self.mode = "heuristic"
        self.model = None
        self.ocr_reader = None
        self._load()

    def _load(self) -> None:
        try:
            from ultralytics import YOLO  # type: ignore

            self.model = YOLO("yolov8n.pt")
            self.mode = "yolo"
        except Exception:
            self.model = None
            self.mode = "heuristic"

        try:
            import easyocr  # type: ignore

            self.ocr_reader = easyocr.Reader(["en"], gpu=False)
        except Exception:
            self.ocr_reader = None

    def detect(self, frame: np.ndarray) -> list[dict[str, Any]]:
        if self.mode == "yolo" and self.model is not None:
            return self._detect_with_yolo(frame)
        return self._heuristic_detect(frame)

    def _detect_with_yolo(self, frame: np.ndarray) -> list[dict[str, Any]]:
        results = self.model.predict(frame, verbose=False, conf=CONFIDENCE_THRESHOLD)
        detections: list[dict[str, Any]] = []
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
            for box in boxes:
                class_id = int(box.cls[0].item())
                label = COCO_CLASS_MAP.get(class_id)
                if label not in SUPPORTED_CLASSES:
                    continue
                confidence = float(box.conf[0].item())
                x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
                detections.append(
                    {
                        "label": label,
                        "confidence": confidence,
                        "bbox": [x1, y1, x2, y2],
                    }
                )
        return detections

    def _heuristic_detect(self, frame: np.ndarray) -> list[dict[str, Any]]:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blur, 60, 180)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        dilated = cv2.dilate(edges, kernel, iterations=1)
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detections: list[dict[str, Any]] = []
        h, w = frame.shape[:2]
        for contour in contours[:60]:
            x, y, cw, ch = cv2.boundingRect(contour)
            area = cw * ch
            if area < 3500 or cw < 40 or ch < 30:
                continue
            if y > h * 0.92 or x > w * 0.95:
                continue
            aspect_ratio = cw / max(ch, 1)
            label = "car"
            if aspect_ratio < 1.0:
                label = "person"
            elif aspect_ratio < 1.5:
                label = "motorcycle"
            elif aspect_ratio > 3.8:
                label = "bus"
            elif aspect_ratio > 2.6:
                label = "truck"
            confidence = min(0.95, 0.45 + (area / (w * h)))
            detections.append(
                {
                    "label": label,
                    "confidence": float(confidence),
                    "bbox": [x, y, x + cw, y + ch],
                }
            )
            if len(detections) >= 14:
                break
        detections.sort(key=lambda item: item["bbox"][2] - item["bbox"][0], reverse=True)
        return detections

    def extract_plate(
        self,
        frame: np.ndarray,
        bbox: list[int],
        fallback_index: int,
    ) -> tuple[str | None, float | None]:
        x1, y1, x2, y2 = bbox
        crop = frame[y1:y2, x1:x2]
        if crop.size == 0:
            return self._fallback_plate(fallback_index), 0.6

        if self.ocr_reader is not None:
            try:
                results = self.ocr_reader.readtext(crop)
                for _, text, score in results:
                    normalized = re.sub(r"[^A-Z0-9]", "", text.upper())
                    if PLATE_REGEX.match(normalized) and score >= PLATE_MIN_CONFIDENCE:
                        return normalized, float(score)
            except Exception:
                pass

        return self._fallback_plate(fallback_index), 0.6

    def _fallback_plate(self, index: int) -> str:
        pool = self.challan_service.known_plates
        return pool[index % len(pool)]


class SourceRuntime:
    def __init__(
        self,
        source: VideoSource,
        detector: DetectorAdapter,
        challan_service: ChallanService,
        logger: DetectionLogger,
    ) -> None:
        self.source = source
        self.detector = detector
        self.challan_service = challan_service
        self.logger = logger
        self._frame_lock = Lock()
        self._metadata_lock = Lock()
        self._stop = Event()
        self._thread: Thread | None = None
        self._latest_frame: bytes | None = None
        self._latest_metadata: dict[str, Any] = {
            "source_id": source.id,
            "source_name": source.name,
            "mode": detector.mode,
            "detections": [],
            "metrics": {
                "fps": 0.0,
                "latency_ms": 0.0,
                "traffic_density": "Low",
                "counts": {},
                "pending_challans": 0,
            },
            "alerts": [],
            "last_updated": None,
        }
        self._plate_cache: dict[str, tuple[str, float]] = {}
        self._last_snapshot_plate: set[str] = set()

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None

    def get_frame(self) -> bytes | None:
        with self._frame_lock:
            return self._latest_frame

    def get_metadata(self) -> dict[str, Any]:
        with self._metadata_lock:
            return dict(self._latest_metadata)

    def _run(self) -> None:
        capture = cv2.VideoCapture(self.source.path)
        capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        frame_index = 0
        prev_time = time.perf_counter()

        while not self._stop.is_set():
            ok, frame = capture.read()
            if not ok:
                capture.release()
                capture = cv2.VideoCapture(self.source.path)
                continue

            frame = self._resize_frame(frame)
            start = time.perf_counter()
            process_frame = frame_index % FRAME_SKIP == 0

            if process_frame:
                detections = self._process_frame(frame, frame_index)
            else:
                detections = self.get_metadata().get("detections", [])

            now = time.perf_counter()
            fps = 1 / max(now - prev_time, 1e-6)
            prev_time = now
            latency_ms = (now - start) * 1000
            annotated = self._draw_overlay(frame.copy(), detections, fps, latency_ms)

            ok, encoded = cv2.imencode(
                ".jpg",
                annotated,
                [int(cv2.IMWRITE_JPEG_QUALITY), STREAM_JPEG_QUALITY],
            )
            if ok:
                with self._frame_lock:
                    self._latest_frame = encoded.tobytes()

            frame_index += 1
            if not process_frame:
                time.sleep(0.005)

        capture.release()

    def _resize_frame(self, frame: np.ndarray) -> np.ndarray:
        height, width = frame.shape[:2]
        if width <= FRAME_WIDTH:
            return frame
        ratio = FRAME_WIDTH / width
        return cv2.resize(frame, (FRAME_WIDTH, int(height * ratio)))

    def _process_frame(self, frame: np.ndarray, frame_index: int) -> list[dict[str, Any]]:
        raw_detections = self.detector.detect(frame)
        enriched: list[dict[str, Any]] = []
        counts: Counter[str] = Counter()
        pending_challans = 0

        for idx, detection in enumerate(raw_detections):
            label = detection["label"]
            counts[label] += 1
            object_id = self._object_id(label, detection["bbox"])
            plate, plate_conf = self._resolve_plate(frame, detection["bbox"], object_id, frame_index, idx)
            challan = self.challan_service.lookup(plate if label in VEHICLE_CLASSES else None)
            if challan.status == "Pending Challan":
                pending_challans += 1
                self._snapshot_if_needed(frame, detection["bbox"], plate, challan)

            timestamp = datetime.now(timezone.utc).isoformat()
            enriched_detection = {
                "object_id": object_id,
                "object_type": label,
                "confidence": round(detection["confidence"], 3),
                "bbox": detection["bbox"],
                "license_plate": plate if label in VEHICLE_CLASSES else None,
                "plate_confidence": round(plate_conf, 3) if plate_conf else None,
                "challan": challan.model_dump() if label in VEHICLE_CLASSES else None,
                "timestamp": timestamp,
            }
            enriched.append(enriched_detection)
            self.logger.log(
                {
                    "timestamp": timestamp,
                    "source_id": self.source.id,
                    "object_id": object_id,
                    "object_type": label,
                    "confidence": round(detection["confidence"], 3),
                    "license_plate": plate if label in VEHICLE_CLASSES else "",
                    "challan_status": challan.status if label in VEHICLE_CLASSES else "",
                    "fine_amount": challan.fine_amount if label in VEHICLE_CLASSES else 0,
                    "violation_type": challan.violation_type if label in VEHICLE_CLASSES else "",
                }
            )

        alerts = self._build_alerts(sum(counts.values()), pending_challans)
        density = self._traffic_density(sum(counts.values()))
        with self._metadata_lock:
            self._latest_metadata = {
                "source_id": self.source.id,
                "source_name": self.source.name,
                "mode": self.detector.mode,
                "detections": enriched,
                "metrics": {
                    "fps": self._latest_metadata.get("metrics", {}).get("fps", 0.0),
                    "latency_ms": self._latest_metadata.get("metrics", {}).get("latency_ms", 0.0),
                    "traffic_density": density,
                    "counts": dict(counts),
                    "pending_challans": pending_challans,
                },
                "alerts": alerts,
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }
        return enriched

    def _resolve_plate(
        self,
        frame: np.ndarray,
        bbox: list[int],
        object_id: str,
        frame_index: int,
        fallback_index: int,
    ) -> tuple[str | None, float | None]:
        if object_id in self._plate_cache and frame_index % OCR_INTERVAL != 0:
            return self._plate_cache[object_id]
        plate, score = self.detector.extract_plate(frame, bbox, fallback_index)
        if plate:
            self._plate_cache[object_id] = (plate, score or 0.6)
        return self._plate_cache.get(object_id, (plate, score))

    def _snapshot_if_needed(
        self,
        frame: np.ndarray,
        bbox: list[int],
        plate: str | None,
        challan: ChallanRecord,
    ) -> None:
        if not plate or challan.status != "Pending Challan" or plate in self._last_snapshot_plate:
            return
        x1, y1, x2, y2 = bbox
        crop = frame[max(y1 - 10, 0): min(y2 + 10, frame.shape[0]), max(x1 - 10, 0): min(x2 + 10, frame.shape[1])]
        snapshot_path = SNAPSHOT_DIR / f"{plate}_{int(time.time())}.jpg"
        cv2.imwrite(str(snapshot_path), crop)
        self._last_snapshot_plate.add(plate)

    def _draw_overlay(
        self,
        frame: np.ndarray,
        detections: list[dict[str, Any]],
        fps: float,
        latency_ms: float,
    ) -> np.ndarray:
        for detection in detections:
            x1, y1, x2, y2 = detection["bbox"]
            label = detection["object_type"]
            confidence = detection["confidence"]
            challan = detection.get("challan") or {}
            color = (61, 214, 140) if challan.get("status") != "Pending Challan" else (65, 105, 225)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            caption = f"{label} {confidence:.2f}"
            cv2.putText(frame, caption, (x1, max(y1 - 12, 18)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
            if detection.get("license_plate"):
                plate_text = detection["license_plate"]
                cv2.putText(frame, plate_text, (x1, min(y2 + 18, frame.shape[0] - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        metrics_text = f"FPS {fps:.1f} | Latency {latency_ms:.1f} ms"
        cv2.putText(frame, metrics_text, (16, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 244, 230), 2)

        with self._metadata_lock:
            if self._latest_metadata.get("metrics"):
                self._latest_metadata["metrics"]["fps"] = round(fps, 2)
                self._latest_metadata["metrics"]["latency_ms"] = round(latency_ms, 2)
        return frame

    def _build_alerts(self, object_count: int, pending_challans: int) -> list[str]:
        alerts: list[str] = []
        if object_count >= HIGH_DENSITY_THRESHOLD:
            alerts.append("Traffic congestion is high on this feed.")
        if pending_challans >= MULTI_CHALLAN_ALERT_THRESHOLD:
            alerts.append("Multiple pending challans detected in the current scene.")
        return alerts

    def _traffic_density(self, object_count: int) -> str:
        if object_count >= HIGH_DENSITY_THRESHOLD:
            return "High"
        if object_count >= 6:
            return "Medium"
        return "Low"

    def _object_id(self, label: str, bbox: list[int]) -> str:
        x1, y1, x2, y2 = bbox
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        return f"{label}-{cx // 32}-{cy // 32}"


class TrafficMonitorService:
    def __init__(
        self,
        sources: list[VideoSource],
        challan_service: ChallanService,
        logger: DetectionLogger,
    ) -> None:
        self.sources = {source.id: source for source in sources}
        self.challan_service = challan_service
        self.logger = logger
        self.detector = DetectorAdapter(challan_service)
        self.runtimes = {
            source.id: SourceRuntime(source, self.detector, challan_service, logger)
            for source in sources
        }
        self.active_source_id = sources[0].id if sources else None
        self._active_lock = Lock()

    def start(self) -> None:
        if self.active_source_id:
            self.runtimes[self.active_source_id].start()

    def stop(self) -> None:
        for runtime in self.runtimes.values():
            runtime.stop()

    def set_active_source(self, source_id: str) -> None:
        if source_id not in self.runtimes:
            raise KeyError(source_id)
        with self._active_lock:
            previous_id = self.active_source_id
            if previous_id == source_id:
                if previous_id:
                    self.runtimes[previous_id].start()
                return
            if previous_id and previous_id in self.runtimes:
                self.runtimes[previous_id].stop()
            self.active_source_id = source_id
            self.runtimes[source_id].start()

    def get_frame(self, source_id: str | None = None) -> bytes | None:
        selected_id = source_id or self.active_source_id
        if not selected_id:
            return None
        return self.runtimes[selected_id].get_frame()

    def get_metadata(self, source_id: str | None = None) -> dict[str, Any]:
        selected_id = source_id or self.active_source_id
        if not selected_id:
            return {}
        metadata = self.runtimes[selected_id].get_metadata()
        metadata["active_source_id"] = self.active_source_id
        return metadata
