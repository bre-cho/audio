from fastapi import APIRouter
from fastapi import APIRouter
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.models.audio_job import AudioJob
from app.schemas.provider import ProviderOut

router = APIRouter()


@router.get('', response_model=list[ProviderOut])
async def list_providers() -> list[ProviderOut]:
    return [
        ProviderOut(code='elevenlabs', name='ElevenLabs', status='active'),
        ProviderOut(code='minimax', name='Minimax', status='active'),
        ProviderOut(code='internal_genvoice', name='Internal GenVoice', status='disabled'),
    ]


@router.get('/health')
def provider_health() -> dict:
    """Check real connectivity to each configured TTS provider.

    Returns per-provider status: ok | no_key | error.
    This endpoint is used for pre-production readiness validation.
    """
    result: dict[str, dict] = {}

    # --- ElevenLabs ---
    api_key = settings.elevenlabs_api_key
    if not api_key:
        result['elevenlabs'] = {'status': 'no_key', 'detail': 'ELEVENLABS_API_KEY not set'}
    else:
        try:
            import httpx
            resp = httpx.get(
                'https://api.elevenlabs.io/v1/user',
                headers={'xi-api-key': api_key},
                timeout=8,
            )
            if resp.status_code == 200:
                result['elevenlabs'] = {'status': 'ok', 'detail': 'authenticated'}
            elif resp.status_code == 401:
                result['elevenlabs'] = {'status': 'error', 'detail': 'invalid API key (401)'}
            else:
                result['elevenlabs'] = {'status': 'error', 'detail': f'HTTP {resp.status_code}'}
        except Exception as exc:
            result['elevenlabs'] = {'status': 'error', 'detail': str(exc)}

    # --- Minimax ---
    minimax_key = getattr(settings, 'minimax_api_key', None)
    if not minimax_key:
        result['minimax'] = {'status': 'no_key', 'detail': 'MINIMAX_API_KEY not set'}
    else:
        result['minimax'] = {'status': 'ok', 'detail': 'key present (connectivity not verified)'}

    # --- Internal GenVoice ---
    result['internal_genvoice'] = {'status': 'placeholder', 'detail': 'no real model; dev/test only'}

    return {'providers': result, 'storage_backend': settings.storage_backend or 'local'}


@router.post('/callback/{provider_code}')
def provider_callback(
    provider_code: str,
    payload: dict,
    db: Session = Depends(get_db),
    x_provider_callback_token: str | None = Header(default=None),
) -> dict:
    """Provider callback to finalize async provider jobs.

    Required payload keys:
    - job_id: UUID string
    - status: done|failed|succeeded
    Optional keys:
    - output_url
    - preview_url
    - error_message
    - provider_payload (dict)
    """
    secret = settings.provider_callback_token
    if secret:
        if not x_provider_callback_token or x_provider_callback_token != secret:
            raise HTTPException(status_code=401, detail='Invalid provider callback token')

    job_id_raw = payload.get('job_id')
    if not job_id_raw:
        raise HTTPException(status_code=400, detail='Missing job_id')
    try:
        job_uuid = UUID(str(job_id_raw))
    except Exception as exc:
        raise HTTPException(status_code=400, detail='Invalid job_id') from exc

    job = db.query(AudioJob).filter(AudioJob.id == job_uuid).one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail='Job not found')

    raw_status = str(payload.get('status', '')).lower().strip()
    if raw_status not in {'done', 'failed', 'succeeded', 'success'}:
        raise HTTPException(status_code=400, detail='Invalid callback status')
    mapped_status = 'done' if raw_status in {'done', 'succeeded', 'success'} else 'failed'

    output_url = payload.get('output_url')
    preview_url = payload.get('preview_url')
    error_message = payload.get('error_message')
    provider_payload = payload.get('provider_payload')

    job.status = mapped_status
    if output_url:
        job.output_url = str(output_url)
    if preview_url:
        job.preview_url = str(preview_url)
    if error_message:
        job.error_message = str(error_message)
    runtime_json = dict(job.runtime_json or {})
    runtime_json['provider_callback'] = {
        'provider': provider_code,
        'status': mapped_status,
        'received_at': datetime.now(UTC).isoformat(),
        'payload': provider_payload or {},
    }
    job.runtime_json = runtime_json
    job.finished_at = datetime.now(UTC)
    job.updated_at = datetime.now(UTC)
    db.commit()

    return {'status': 'ok', 'job_id': str(job.id), 'job_status': job.status}
