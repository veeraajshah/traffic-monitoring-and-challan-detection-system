from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


VehicleType = Literal["all", "car", "motorcycle", "bus", "truck", "person"]


class VideoSource(BaseModel):
    id: str
    name: str
    path: str


class VideoSelection(BaseModel):
    source_id: str = Field(..., description="Selected source identifier")


class ChallanRecord(BaseModel):
    plate: str
    status: Literal["No Challan", "Pending Challan"]
    fine_amount: int
    violation_type: str
    violation_date: str | None = None


class DetectionRecord(BaseModel):
    object_id: str
    object_type: str
    confidence: float
    bbox: list[int]
    license_plate: str | None = None
    plate_confidence: float | None = None
    challan: ChallanRecord | None = None
    timestamp: str

