from fastapi import APIRouter
from app.api import (
	affiliate,
	ai_effects,
	audio,
	baselines,
	billing,
	conversation,
	decisions,
	jobs,
	observability,
	projects,
	providers,
	recovery,
	remediation,
	tts,
	voice_clone,
	voices,
)

api_router = APIRouter()
api_router.include_router(audio.router, prefix='/audio', tags=['audio'])
api_router.include_router(providers.router, prefix='/providers', tags=['providers'])
api_router.include_router(voices.router, prefix='/voices', tags=['voices'])
api_router.include_router(tts.router, prefix='/tts', tags=['tts'])
api_router.include_router(conversation.router, prefix='/conversation', tags=['conversation'])
api_router.include_router(voice_clone.router, prefix='/voice-clone', tags=['voice-clone'])
api_router.include_router(projects.router, prefix='/projects', tags=['projects'])
api_router.include_router(jobs.router, prefix='/jobs', tags=['jobs'])
api_router.include_router(baselines.router, prefix='/baselines', tags=['baselines'])
api_router.include_router(decisions.router, prefix='/decisions', tags=['decisions'])
api_router.include_router(remediation.router, prefix='/remediation', tags=['remediation'])
api_router.include_router(recovery.router, prefix='/recovery', tags=['recovery'])
api_router.include_router(billing.router, prefix='/billing', tags=['billing'])
api_router.include_router(observability.router, prefix='/observability', tags=['observability'])
api_router.include_router(affiliate.router, prefix='/affiliate', tags=['affiliate'])
api_router.include_router(ai_effects.router, tags=['ai-effects'])
