"""Dau cuoi API cho theo doi va metric am thanh."""

from datetime import UTC, datetime
from typing import Dict

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.audio_job import AudioJob

router = APIRouter()


def _collect_audio_metrics(db: Session) -> Dict[str, float]:
    """Thu thap metric he thong am thanh cho Prometheus."""
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
    """Tra ve metric theo dinh dang van ban cua Prometheus."""
    metrics = _collect_audio_metrics(db)

    lines = [
        "# HELP audio_voice_clone_queue_depth Do sau hien tai cua hang doi clone giong noi",
        "# TYPE audio_voice_clone_queue_depth gauge",
        f'audio_voice_clone_queue_depth {metrics["audio_voice_clone_queue_depth"]}',
        "",
        "# HELP audio_narration_queue_depth Do sau hien tai cua hang doi thuyet minh",
        "# TYPE audio_narration_queue_depth gauge",
        f'audio_narration_queue_depth {metrics["audio_narration_queue_depth"]}',
        "",
        "# HELP audio_audio_mix_queue_depth Do sau hien tai cua hang doi tron am thanh",
        "# TYPE audio_audio_mix_queue_depth gauge",
        f'audio_audio_mix_queue_depth {metrics["audio_audio_mix_queue_depth"]}',
        "",
        "# HELP audio_jobs_stuck_total Tong so job am thanh bi ket",
        "# TYPE audio_jobs_stuck_total gauge",
        f'audio_jobs_stuck_total {metrics["audio_jobs_stuck_total"]}',
        "",
        "# HELP audio_preview_last_success_timestamp_seconds Moc thoi gian preview thanh cong gan nhat",
        "# TYPE audio_preview_last_success_timestamp_seconds gauge",
        f'audio_preview_last_success_timestamp_seconds {metrics["audio_preview_last_success_timestamp_seconds"]}',
        "",
        "# HELP audio_narration_last_success_timestamp_seconds Moc thoi gian thuyet minh thanh cong gan nhat",
        "# TYPE audio_narration_last_success_timestamp_seconds gauge",
        f'audio_narration_last_success_timestamp_seconds {metrics["audio_narration_last_success_timestamp_seconds"]}',
        "",
        "# HELP audio_clone_last_success_timestamp_seconds Moc thoi gian clone thanh cong gan nhat",
        "# TYPE audio_clone_last_success_timestamp_seconds gauge",
        f'audio_clone_last_success_timestamp_seconds {metrics["audio_clone_last_success_timestamp_seconds"]}',
        "",
        "# HELP audio_clone_preview_last_success_timestamp_seconds Moc thoi gian preview clone thanh cong gan nhat",
        "# TYPE audio_clone_preview_last_success_timestamp_seconds gauge",
        f'audio_clone_preview_last_success_timestamp_seconds {metrics["audio_clone_preview_last_success_timestamp_seconds"]}',
    ]

    return "\n".join(lines) + "\n"
