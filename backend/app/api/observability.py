"""Audio observability and metrics endpoints."""

from datetime import UTC, datetime
from typing import Dict

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.audio_job import AudioJob

router = APIRouter()


def _collect_audio_metrics(db: Session) -> Dict[str, float]:
    """Collect audio system metrics for Prometheus."""
    now = datetime.now(UTC)
    now_ts = now.timestamp()

    # Queue depth metrics
    queued = db.query(func.count(AudioJob.id)).filter(AudioJob.status == "queued").scalar() or 0
    processing = db.query(func.count(AudioJob.id)).filter(AudioJob.status == "processing").scalar() or 0
    failed = db.query(func.count(AudioJob.id)).filter(AudioJob.status == "failed").scalar() or 0

    # Job counts by type
    tts_jobs = db.query(func.count(AudioJob.id)).filter(AudioJob.job_type == "tts_preview").scalar() or 0
    narration_jobs = db.query(func.count(AudioJob.id)).filter(AudioJob.job_type == "narration").scalar() or 0
    clone_jobs = db.query(func.count(AudioJob.id)).filter(AudioJob.job_type == "clone").scalar() or 0

    # Success timestamps
    def _last_success(job_type: str) -> float:
        row = (
            db.query(func.max(AudioJob.updated_at))
            .filter(AudioJob.job_type == job_type, AudioJob.status.in_(["done", "succeeded", "success"]))
            .scalar()
        )
        if row is None:
            return 0.0
        ts = row.replace(tzinfo=UTC).timestamp() if row.tzinfo is None else row.timestamp()
        return ts

    return {
        "audio_voice_clone_queue_depth": float(clone_jobs),
        "audio_narration_queue_depth": float(narration_jobs),
        "audio_audio_mix_queue_depth": float(processing),
        "audio_jobs_stuck_total": float(failed),
        "audio_preview_last_success_timestamp_seconds": _last_success("tts_preview"),
        "audio_narration_last_success_timestamp_seconds": _last_success("narration"),
        "audio_clone_last_success_timestamp_seconds": _last_success("clone"),
        "audio_clone_preview_last_success_timestamp_seconds": _last_success("clone_preview"),
    }


@router.get("/prometheus")
def prometheus_metrics(db: Session = Depends(get_db)) -> str:
    """Expose metrics in Prometheus text format."""
    metrics = _collect_audio_metrics(db)

    lines = [
        "# HELP audio_voice_clone_queue_depth Current depth of voice clone queue",
        "# TYPE audio_voice_clone_queue_depth gauge",
        f'audio_voice_clone_queue_depth {metrics["audio_voice_clone_queue_depth"]}',
        "",
        "# HELP audio_narration_queue_depth Current depth of narration queue",
        "# TYPE audio_narration_queue_depth gauge",
        f'audio_narration_queue_depth {metrics["audio_narration_queue_depth"]}',
        "",
        "# HELP audio_audio_mix_queue_depth Current depth of audio mix queue",
        "# TYPE audio_audio_mix_queue_depth gauge",
        f'audio_audio_mix_queue_depth {metrics["audio_audio_mix_queue_depth"]}',
        "",
        "# HELP audio_jobs_stuck_total Total stuck audio jobs",
        "# TYPE audio_jobs_stuck_total gauge",
        f'audio_jobs_stuck_total {metrics["audio_jobs_stuck_total"]}',
        "",
        "# HELP audio_preview_last_success_timestamp_seconds Last successful preview timestamp",
        "# TYPE audio_preview_last_success_timestamp_seconds gauge",
        f'audio_preview_last_success_timestamp_seconds {metrics["audio_preview_last_success_timestamp_seconds"]}',
        "",
        "# HELP audio_narration_last_success_timestamp_seconds Last successful narration timestamp",
        "# TYPE audio_narration_last_success_timestamp_seconds gauge",
        f'audio_narration_last_success_timestamp_seconds {metrics["audio_narration_last_success_timestamp_seconds"]}',
        "",
        "# HELP audio_clone_last_success_timestamp_seconds Last successful clone timestamp",
        "# TYPE audio_clone_last_success_timestamp_seconds gauge",
        f'audio_clone_last_success_timestamp_seconds {metrics["audio_clone_last_success_timestamp_seconds"]}',
        "",
        "# HELP audio_clone_preview_last_success_timestamp_seconds Last successful clone preview timestamp",
        "# TYPE audio_clone_preview_last_success_timestamp_seconds gauge",
        f'audio_clone_preview_last_success_timestamp_seconds {metrics["audio_clone_preview_last_success_timestamp_seconds"]}',
    ]

    return "\n".join(lines) + "\n"
