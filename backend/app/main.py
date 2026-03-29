from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from time import sleep

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from app.config import APP_DATA_DIR, LOG_DIR, SNAPSHOT_DIR
from app.models import VehicleType, VideoSelection
from app.services.challan_service import ChallanService
from app.services.detection_engine import TrafficMonitorService
from app.services.logger_service import DetectionLogger
from app.services.video_registry import VideoRegistry

video_registry = VideoRegistry()
challan_service = ChallanService(APP_DATA_DIR / "challans.json")
logger = DetectionLogger()
traffic_service = TrafficMonitorService(video_registry.list_sources(), challan_service, logger)


@asynccontextmanager
async def lifespan(_: FastAPI):
    traffic_service.start()
    yield
    traffic_service.stop()


app = FastAPI(
    title="Traffic Monitoring and Challan Detection API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/snapshot_files", StaticFiles(directory=SNAPSHOT_DIR), name="snapshot_files")


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/get_videos")
def get_videos() -> dict[str, object]:
    sources = [source.model_dump() for source in video_registry.list_sources()]
    return {
        "videos": sources,
        "active_source_id": traffic_service.active_source_id,
    }


@app.post("/set_video")
def set_video(selection: VideoSelection) -> dict[str, str]:
    try:
        traffic_service.set_active_source(selection.source_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown source: {selection.source_id}") from exc
    return {"message": "Active source updated", "active_source_id": selection.source_id}


@app.get("/video_feed")
def video_feed(source_id: str | None = None) -> StreamingResponse:
    def generate():
        while True:
            frame = traffic_service.get_frame(source_id)
            if not frame:
                sleep(0.05)
                continue
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
            )

    return StreamingResponse(generate(), media_type="multipart/x-mixed-replace; boundary=frame")


@app.get("/metadata")
def metadata(
    source_id: str | None = None,
    vehicle_type: VehicleType = Query("all"),
) -> dict[str, object]:
    data = traffic_service.get_metadata(source_id)
    detections = data.get("detections", [])
    if vehicle_type != "all":
        detections = [item for item in detections if item["object_type"] == vehicle_type]
    data["detections"] = detections
    data["selected_vehicle_type"] = vehicle_type
    return data


@app.get("/check_challan/{plate}")
def check_challan(plate: str):
    return challan_service.lookup(plate).model_dump()


@app.get("/export_logs")
def export_logs(format: str = Query("csv", pattern="^(csv|json)$")):
    file_name = "detections.csv" if format == "csv" else "detections.json"
    file_path = LOG_DIR / file_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="No logs available yet")
    media_type = "text/csv" if format == "csv" else "application/json"
    return FileResponse(path=file_path, media_type=media_type, filename=file_name)


@app.get("/snapshots")
def list_snapshots() -> dict[str, list[str]]:
    files = [str(path.name) for path in sorted(Path(SNAPSHOT_DIR).glob("*.jpg"))]
    return {"snapshots": files}
