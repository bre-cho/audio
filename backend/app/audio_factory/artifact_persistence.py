from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.audio_factory.schemas import AudioArtifactContract
from app.models.audio_output import AudioOutput


class ArtifactPersistenceService:
    def persist(
        self,
        *,
        db: Session,
        job_id: str,
        contracts: list[AudioArtifactContract],
    ) -> list[AudioOutput]:
        job_uuid = UUID(job_id)
        db.query(AudioOutput).filter(AudioOutput.job_id == job_uuid).delete(synchronize_session=False)

        rows: list[AudioOutput] = []
        for contract in contracts:
            row = AudioOutput(
                job_id=job_uuid,
                source_job_id=job_uuid,
                artifact_id=contract.artifact_id,
                output_type=contract.artifact_type,
                artifact_type=contract.artifact_type,
                storage_key=contract.storage_key,
                public_url=contract.public_url,
                mime_type=contract.mime_type,
                duration_ms=500,
                size_bytes=contract.size_bytes,
                checksum=contract.checksum,
                input_hash=contract.input_hash,
                provider=contract.provider,
                model_version=contract.model_version,
                template_version=contract.template_version,
                runtime_version=contract.runtime_version,
                promotion_status="persisted",
                waveform_json=contract.waveform_json or contract.model_dump(),
                metadata_json=contract.metadata,
            )
            db.add(row)
            rows.append(row)

        db.commit()
        for row in rows:
            db.refresh(row)
        return rows