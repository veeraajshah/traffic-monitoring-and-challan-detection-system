from __future__ import annotations

import json
from pathlib import Path

from app.config import APP_DATA_DIR
from app.models import ChallanRecord


class ChallanService:
    def __init__(self, file_path: Path | None = None) -> None:
        self.file_path = file_path or APP_DATA_DIR / "challans.json"
        self._records = self._load_records()
        self._plate_pool = list(self._records.keys())

    def _load_records(self) -> dict[str, ChallanRecord]:
        with self.file_path.open("r", encoding="utf-8") as handle:
            records = json.load(handle)
        return {
            item["plate"]: ChallanRecord(**item)
            for item in records
        }

    @property
    def known_plates(self) -> list[str]:
        return self._plate_pool

    def lookup(self, plate: str | None) -> ChallanRecord:
        if not plate:
            return ChallanRecord(
                plate="UNKNOWN",
                status="No Challan",
                fine_amount=0,
                violation_type="None",
                violation_date=None,
            )
        normalized = plate.replace(" ", "").upper()
        return self._records.get(
            normalized,
            ChallanRecord(
                plate=normalized,
                status="No Challan",
                fine_amount=0,
                violation_type="None",
                violation_date=None,
            ),
        )

