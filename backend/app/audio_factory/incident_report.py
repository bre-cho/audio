from __future__ import annotations

import time
import traceback


class IncidentReportService:
    def build_failure_incident(
        self,
        *,
        workflow_type: str,
        job_id: str,
        error: Exception,
        started_at: float,
    ) -> dict:
        return {
            "incident_type": "audio_factory_failure",
            "severity": "high",
            "job_id": job_id,
            "workflow_type": workflow_type,
            "duration_ms": int((time.time() - started_at) * 1000),
            "error_type": error.__class__.__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "recommended_action": self._recommend(error),
        }

    def _recommend(self, error: Exception) -> str:
        name = error.__class__.__name__

        if name == "SchemaGuardError":
            return "Run migration or update DB schema before deploy."
        if name == "ArtifactValidationError":
            return "Check artifact generation, checksum, storage write, and DB persistence."
        if name == "FileNotFoundError":
            return "Check provider output path and storage handoff."
        return "Inspect worker logs and factory report."