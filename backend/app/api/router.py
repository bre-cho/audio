from fastapi import APIRouter
from app.api import (
	affiliate,
	ai_effects,
	audio,
	audio_quality,
	baselines,
	billing,
	conversation,
	decisions,
	jobs,
	library,
	noise_reducer,
	observability,
	podcast,
	projects,
	providers,
	recovery,
	remediation,
	sound_effects,
	storage_health,
	tts,
	voice_changer,
	voice_clone,
	voice_design,
	voice_enhancer,
	voices,
)
api_router = APIRouter()
api_router.include_router(audio.router, prefix='/audio', tags=['audio'])
api_router.include_router(providers.router, prefix='/providers', tags=['providers'])
api_router.include_router(voices.router, prefix='/voices', tags=['voices'])
api_router.include_router(tts.router, prefix='/tts', tags=['tts'])
api_router.include_router(conversation.router, prefix='/conversation', tags=['conversation'])
api_router.include_router(voice_clone.router, prefix='/voice-clone', tags=['voice-clone'])
api_router.include_router(voice_changer.router, tags=['voice-changer'])
api_router.include_router(voice_design.router, tags=['voice-design'])
api_router.include_router(noise_reducer.router, tags=['noise-reducer'])
api_router.include_router(voice_enhancer.router, tags=['voice-enhancer'])
api_router.include_router(sound_effects.router, tags=['sound-effects'])
api_router.include_router(podcast.router, tags=['podcast'])
api_router.include_router(audio_quality.router, tags=['audio-quality'])
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
api_router.include_router(library.router, tags=['library'])
api_router.include_router(storage_health.router, tags=['storage'])
