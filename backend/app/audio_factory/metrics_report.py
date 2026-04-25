from __future__ import annotations

import time

from app.audio_factory.schemas import AudioArtifactContract


class MetricsReportService:
    def build_success_metrics(
        self,
        *,
        workflow_type: str,
        job_id: str,
        started_at: float,
        artifacts: list[AudioArtifactContract],
    ) -> dict:
        return {
            "job_id": job_id,
            "workflow_type": workflow_type,
            "status": "succeeded",
            "duration_ms": int((time.time() - started_at) * 1000),
            "artifact_count": len(artifacts),
            "artifact_ids": [artifact.artifact_id for artifact in artifacts],
            "promotion_statuses": [artifact.promotion_status for artifact in artifacts],
        }

    def build_failure_metrics(
        self,
        *,
        workflow_type: str,
        job_id: str,
        started_at: float,
        error: Exception,
    ) -> dict:
        return {
            "job_id": job_id,
            "workflow_type": workflow_type,
            "status": "failed",
            "duration_ms": int((time.time() - started_at) * 1000),
            "error_type": error.__class__.__name__,
            "error_message": str(error),
        }