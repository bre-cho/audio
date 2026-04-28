# audio
code clone giọng noi

## Production config (S3 + API auth token)

Backend đọc cấu hình qua [backend/.env.example](backend/.env.example) và [backend/app/core/config.py](backend/app/core/config.py).

### 1. S3 object storage

Đặt các biến môi trường sau:

```env
STORAGE_BACKEND=s3
S3_BUCKET=audio-assets
S3_REGION=ap-southeast-1
S3_ENDPOINT_URL=
S3_PUBLIC_BASE_URL=https://cdn.example.com/audio-assets
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_SESSION_TOKEN=
```

Ghi chú:
- `S3_ENDPOINT_URL` để trống khi dùng AWS S3 thật, set URL khi dùng MinIO.
- `S3_PUBLIC_BASE_URL` là URL public trả về cho client (CDN hoặc bucket public domain).

### 2. API Bearer token auth

```env
AUTH_ENABLED=true
JWT_SECRET_KEY=replace_me
JWT_ALGORITHM=HS256
JWT_AUDIENCE=
JWT_ISSUER=
API_AUTH_TOKENS=
DEFAULT_USER_ID=00000000-0000-0000-0000-000000000001
```

Khi `AUTH_ENABLED=true`, API yêu cầu header:

```bash
Authorization: Bearer <token>
```

Ưu tiên production:
- Dùng JWT và truyền `sub` (hoặc `user_id`) là UUID người dùng.

Fallback:
- Nếu không dùng JWT, có thể set `API_AUTH_TOKENS` theo các dạng:
  - `token`
  - `token:user_uuid`
  - `token:user_uuid:scope1|scope2`
  - `token:user_uuid:scope1|scope2:role1|role2`

Gợi ý scope/role:
- Endpoint khởi tạo effect mặc định yêu cầu scope `ai-effects.init-defaults` hoặc role `admin`.

### 3. Verify hẹp sau khi deploy

```bash
cd backend && alembic current
cd backend && ARTIFACT_ROOT=/tmp/artifacts python -m pytest tests/test_affiliate_e2e.py -q
cd backend && ARTIFACT_ROOT=/tmp/artifacts python -m pytest tests/test_audio_route_task_mapping.py -q
cd frontend && npm run build
```

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
