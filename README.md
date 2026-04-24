# audio
code clone giọng noi

## Backend structure

```text
backend/
 └── app/
	 ├── main.py
	 ├── api/
	 │   ├── billing.py
	 │   ├── conversation.py
	 │   ├── deps.py
	 │   ├── jobs.py
	 │   ├── projects.py
	 │   ├── providers.py
	 │   ├── router.py
	 │   ├── tts.py
	 │   ├── voice_clone.py
	 │   └── voices.py
	 ├── core/
	 │   ├── config.py
	 │   ├── credits.py
	 │   └── storage.py
	 ├── db/
	 │   ├── base.py
	 │   └── session.py
	 ├── models/
	 │   ├── audio_job.py
	 │   ├── audio_output.py
	 │   ├── credit_ledger.py
	 │   ├── project.py
	 │   ├── provider.py
	 │   ├── script_asset.py
	 │   └── voice.py
	 ├── providers/
	 │   ├── base.py
	 │   ├── elevenlabs.py
	 │   ├── internal_genvoice.py
	 │   └── minimax.py
	 ├── repositories/
	 │   ├── credit_repo.py
	 │   ├── job_repo.py
	 │   ├── project_repo.py
	 │   └── voice_repo.py
	 ├── schemas/
	 │   ├── billing.py
	 │   ├── conversation.py
	 │   ├── job.py
	 │   ├── project.py
	 │   ├── provider.py
	 │   ├── tts.py
	 │   ├── voice.py
	 │   └── voice_clone.py
	 ├── services/
	 │   ├── audio_provider_router.py
	 │   ├── billing_service.py
	 │   ├── conversation_service.py
	 │   ├── job_service.py
	 │   ├── project_service.py
	 │   ├── provider_router.py
	 │   ├── tts_service.py
	 │   ├── voice_clone_service.py
	 │   └── audio/
	 │       ├── preview_storage_helper.py
	 │       ├── provider_base.py
	 │       └── providers/
	 │           ├── elevenlabs_provider.py
	 │           └── minimax_provider.py
	 ├── utils/
	 │   ├── script_parser.py
	 │   └── text_normalizer.py
	 └── workers/
		 ├── audio_tasks.py
		 ├── celery_app.py
		 └── clone_tasks.py
```
