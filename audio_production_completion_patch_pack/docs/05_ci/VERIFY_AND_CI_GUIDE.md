# VERIFY AND CI GUIDE

## Mục tiêu
CI phải bắt được pass giả, silent artifact, provider mock, migration thiếu bảng, worker không chạy end-to-end.

## 1. Test bắt buộc

### 1.1 Provider strict mode test
- Set `ENV=production`, `PROVIDER_STRICT_MODE=true`.
- Submit TTS với `internal_genvoice`.
- Expected: failed/blocked, không tạo promoted artifact.

### 1.2 Silent WAV block test
- Tạo silent WAV.
- Run artifact validation.
- Expected: `audio_contains_signal=false`, `promotion_status=blocked`.

### 1.3 Real provider capability test
- Gọi `/providers`.
- Verify `minimax.production_ready=false` nếu chưa implement.
- Verify `internal_genvoice.production_ready=false`.

### 1.4 Worker E2E test
- Submit job.
- Worker xử lý.
- DB status: queued → processing → succeeded/failed.
- Artifact có checksum + quality report.

### 1.5 Migration test
- Fresh Postgres.
- Alembic upgrade head.
- Run API smoke.
- Run worker smoke.
- Run downgrade/upgrade nếu repo đang có policy lineage.

## 2. Script đề xuất

```text
scripts/ci/verify_audio_truth_gate.sh
scripts/ci/verify_provider_capabilities.sh
scripts/ci/verify_audio_signal_validation.py
scripts/ci/verify_worker_e2e.sh
scripts/ci/verify_frontend_api_parity.py
```

## 3. CI hard gates
Build fail nếu:
- Có `internal_genvoice` promoted trong production.
- Có artifact `generation_mode=placeholder` mà status succeeded.
- Có provider `queued` giả cho clone mà không có `external_voice_id`.
- Có route frontend gọi endpoint không tồn tại.
- Có DB model nhưng thiếu migration.
- Có migration nhiều heads mà không merge.

## 4. Report format
Mỗi verify script ghi append vào:
`artifacts/verify/audio_production_verify_report.txt`

Không được ghi đè report giữa các bước.
