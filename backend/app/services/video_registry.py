from __future__ import annotations

from pathlib import Path

from app.config import DATA_DIR, VIDEO_EXTENSIONS
from app.models import VideoSource


class VideoRegistry:
    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = data_dir or DATA_DIR
        self._sources = self._discover_sources()

    def _discover_sources(self) -> list[VideoSource]:
        sources: list[VideoSource] = []
        for file_path in sorted(self.data_dir.iterdir()):
            if file_path.suffix.lower() not in VIDEO_EXTENSIONS:
                continue
            source_id = file_path.stem.lower().replace(" ", "-").replace("(", "").replace(")", "")
            sources.append(
                VideoSource(
                    id=source_id,
                    name=file_path.stem,
                    path=str(file_path),
                )
            )
        return sources

    def list_sources(self) -> list[VideoSource]:
        return self._sources

    def get_source(self, source_id: str) -> VideoSource:
        for source in self._sources:
            if source.id == source_id:
                return source
        raise KeyError(f"Unknown source_id: {source_id}")

