# MIGRATION GUIDE

## Bảng/field cần bổ sung

### audio_outputs hoặc artifacts table
Thêm:
```sql
ALTER TABLE audio_outputs ADD COLUMN IF NOT EXISTS generation_mode VARCHAR(32) DEFAULT 'unknown';
ALTER TABLE audio_outputs ADD COLUMN IF NOT EXISTS provider_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE audio_outputs ADD COLUMN IF NOT EXISTS audio_contains_signal BOOLEAN DEFAULT FALSE;
ALTER TABLE audio_outputs ADD COLUMN IF NOT EXISTS signal_rms INTEGER;
ALTER TABLE audio_outputs ADD COLUMN IF NOT EXISTS signal_peak INTEGER;
ALTER TABLE audio_outputs ADD COLUMN IF NOT EXISTS quality_report JSONB;
```

### voices table
Thêm:
```sql
ALTER TABLE voices ADD COLUMN IF NOT EXISTS external_voice_id VARCHAR(255);
ALTER TABLE voices ADD COLUMN IF NOT EXISTS provider_status VARCHAR(64);
ALTER TABLE voices ADD COLUMN IF NOT EXISTS consent_status VARCHAR(64);
ALTER TABLE voices ADD COLUMN IF NOT EXISTS sample_count INTEGER DEFAULT 0;
ALTER TABLE voices ADD COLUMN IF NOT EXISTS preview_artifact_id VARCHAR(255);
```

### provider_capabilities table nếu muốn persistence
```sql
CREATE TABLE IF NOT EXISTS provider_capabilities (
  id SERIAL PRIMARY KEY,
  provider VARCHAR(64) NOT NULL,
  capability VARCHAR(64) NOT NULL,
  production_ready BOOLEAN DEFAULT FALSE,
  enabled BOOLEAN DEFAULT FALSE,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now(),
  UNIQUE(provider, capability)
);
```

## Alembic rule
- Không sửa migration cũ nếu đã chạy ở môi trường thật.
- Tạo revision mới dạng additive.
- CI phải chạy fresh Postgres upgrade head.
