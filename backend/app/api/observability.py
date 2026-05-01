"""API endpoint for observability and audio metrics."""

from datetime import UTC, datetime, timedelta
from typing import Dict

from fastapi import APIRouter, Depends
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.audio_job import AudioJob
from app.models.credit_ledger import CreditLedger

router = APIRouter()


def _collect_audio_metrics(db: Session) -> Dict[str, float]:
    """Collect system audio metrics for Prometheus."""
    now = datetime.now(UTC)

    # Queue depth metrics
    queued = db.query(func.count(AudioJob.id)).filter(AudioJob.status == "queued").scalar() or 0
    processing = db.query(func.count(AudioJob.id)).filter(AudioJob.status == "processing").scalar() or 0
    failed = db.query(func.count(AudioJob.id)).filter(AudioJob.status == "failed").scalar() or 0

    # Job counts by type
    tts_jobs = db.query(func.count(AudioJob.id)).filter(AudioJob.job_type == "tts_preview").scalar() or 0
    narration_jobs = db.query(func.count(AudioJob.id)).filter(AudioJob.job_type == "narration").scalar() or 0
    clone_jobs = db.query(func.count(AudioJob.id)).filter(AudioJob.job_type == "clone").scalar() or 0
    effect_jobs = db.query(func.count(AudioJob.id)).filter(AudioJob.job_type == "audio_effect").scalar() or 0

    # Total job counts for error rate calculation
    total_jobs_24h = db.query(func.count(AudioJob.id)).filter(
        AudioJob.created_at >= now - timedelta(hours=24)
    ).scalar() or 0
    failed_24h = db.query(func.count(AudioJob.id)).filter(
        AudioJob.created_at >= now - timedelta(hours=24),
        AudioJob.status == "failed",
    ).scalar() or 0
    succeeded_24h = db.query(func.count(AudioJob.id)).filter(
        AudioJob.created_at >= now - timedelta(hours=24),
        AudioJob.status.in_(["succeeded", "done", "success"]),
    ).scalar() or 0

    # Provider error breakdown
    provider_errors: dict[str, int] = {}
    try:
        rows = (
            db.query(
                func.coalesce(AudioJob.error_code, "unknown").label("err"),
                func.count(AudioJob.id).label("cnt"),
            )
            .filter(AudioJob.status == "failed", AudioJob.created_at >= now - timedelta(hours=24))
            .group_by(text("err"))
            .all()
        )
        for row in rows:
            provider_errors[row.err] = int(row.cnt)
    except Exception:
        pass

    # Job latency: avg seconds from created_at to finished_at for succeeded jobs in last 24 h
    avg_latency_sec = 0.0
    try:
        latency = db.query(
            func.avg(func.extract("epoch", AudioJob.finished_at - AudioJob.created_at))
        ).filter(
            AudioJob.status.in_(["succeeded", "done", "success"]),
            AudioJob.finished_at.isnot(None),
            AudioJob.created_at >= now - timedelta(hours=24),
        ).scalar()
        avg_latency_sec = float(latency or 0.0)
    except Exception:
        pass

    # Credit consumption in last 24 h
    credits_consumed_24h = 0
    try:
        result = db.query(
            func.coalesce(func.sum(func.abs(CreditLedger.delta_credits)), 0)
        ).filter(
            CreditLedger.event_type == "reserve",
            CreditLedger.created_at >= now - timedelta(hours=24),
        ).scalar()
        credits_consumed_24h = int(result or 0)
    except Exception:
        pass

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
        "audio_jobs_queued": float(queued),
        "audio_jobs_processing": float(processing),
        "audio_jobs_failed_total": float(failed),
        "audio_voice_clone_queue_depth": float(clone_jobs),
        "audio_narration_queue_depth": float(narration_jobs),
        "audio_tts_preview_queue_depth": float(tts_jobs),
        "audio_effect_queue_depth": float(effect_jobs),
        "audio_audio_mix_queue_depth": float(processing),
        "audio_jobs_stuck_total": float(failed),
        # 24-hour rates
        "audio_jobs_total_24h": float(total_jobs_24h),
        "audio_jobs_failed_24h": float(failed_24h),
        "audio_jobs_succeeded_24h": float(succeeded_24h),
        "audio_error_rate_24h": float(failed_24h / total_jobs_24h) if total_jobs_24h > 0 else 0.0,
        # Latency
        "audio_job_avg_latency_seconds": avg_latency_sec,
        # Credits
        "audio_credits_consumed_24h": float(credits_consumed_24h),
        # Last success timestamps
        "audio_preview_last_success_timestamp_seconds": _last_success("tts_preview"),
        "audio_narration_last_success_timestamp_seconds": _last_success("narration"),
        "audio_clone_last_success_timestamp_seconds": _last_success("clone"),
        "audio_clone_preview_last_success_timestamp_seconds": _last_success("clone_preview"),
    }


def _prom_lines(name: str, help_text: str, metric_type: str, value: float) -> list[str]:
    return [
        f"# HELP {name} {help_text}",
        f"# TYPE {name} {metric_type}",
        f"{name} {value}",
        "",
    ]


@router.get("/prometheus")
def prometheus_metrics(db: Session = Depends(get_db)) -> str:
    """Return metrics in Prometheus text format."""
    metrics = _collect_audio_metrics(db)

    lines: list[str] = []
    defs = [
        ("audio_jobs_queued", "Current number of queued audio jobs", "gauge"),
        ("audio_jobs_processing", "Current number of audio jobs in processing", "gauge"),
        ("audio_jobs_failed_total", "Total failed audio jobs (all time)", "gauge"),
        ("audio_voice_clone_queue_depth", "Current queue depth for voice clone jobs", "gauge"),
        ("audio_narration_queue_depth", "Current queue depth for narration jobs", "gauge"),
        ("audio_tts_preview_queue_depth", "Current queue depth for TTS preview jobs", "gauge"),
        ("audio_effect_queue_depth", "Current queue depth for audio effect jobs", "gauge"),
        ("audio_audio_mix_queue_depth", "Current queue depth for audio mix jobs", "gauge"),
        ("audio_jobs_stuck_total", "Total number of stuck audio jobs", "gauge"),
        ("audio_jobs_total_24h", "Total audio jobs submitted in the last 24 hours", "gauge"),
        ("audio_jobs_failed_24h", "Failed audio jobs in the last 24 hours", "gauge"),
        ("audio_jobs_succeeded_24h", "Succeeded audio jobs in the last 24 hours", "gauge"),
        ("audio_error_rate_24h", "Job error rate over the last 24 hours (0.0–1.0)", "gauge"),
        ("audio_job_avg_latency_seconds", "Average job processing latency in seconds (24h)", "gauge"),
        ("audio_credits_consumed_24h", "Credits reserved/consumed in the last 24 hours", "gauge"),
        ("audio_preview_last_success_timestamp_seconds", "Unix timestamp of last successful TTS preview", "gauge"),
        ("audio_narration_last_success_timestamp_seconds", "Unix timestamp of last successful narration", "gauge"),
        ("audio_clone_last_success_timestamp_seconds", "Unix timestamp of last successful voice clone", "gauge"),
        ("audio_clone_preview_last_success_timestamp_seconds", "Unix timestamp of last successful clone preview", "gauge"),
    ]

    for name, help_text, metric_type in defs:
        value = metrics.get(name, 0.0)
        lines.extend(_prom_lines(name, help_text, metric_type, value))

    return "\n".join(lines) + "\n"
