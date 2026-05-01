from __future__ import annotations

from pathlib import Path


class PodcastExportService:
    def validate_export(self, output_path: str) -> dict:
        p = Path(output_path)
        if not p.exists() or p.stat().st_size == 0:
            raise RuntimeError("podcast_export_missing_or_empty")
        return {"output_path": str(p), "size_bytes": p.stat().st_size, "export_pass": True}
