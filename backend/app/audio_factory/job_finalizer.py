from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.audio_factory.schemas import AudioArtifactContract, AudioFactoryResult
from app.models.audio_job import AudioJob
from app.models.audio_output import AudioOutput


class AudioJobFinalizerError(RuntimeError):
    pass


class AudioJobFinalizer:
    """Single success gate for audio jobs.

    This class is intentionally stricter than the workers. Workers may run the
    provider/factory, but only this finalizer is allowed to mark a job as
    succeeded. The success contract is:

    - factory execution succeeded
    - artifacts are non-empty
    - file validation passed
    - DB persistence validation passed
    - each artifact has a verified/persisted promotion state
    - each artifact has a matching audio_outputs row with persisted status
    """

    VERIFIED_STATUSES = {"contract_verified", "persisted"}

    def finalize_success(
        self,
        *,
        db: Session,
        job_id: str,
        execution: AudioFactoryResult,
        promotion_reason: str,
        provider: str = "internal_genvoice",
    ) -> AudioJob:
        job_uuid = UUID(job_id)
        job = db.query(AudioJob).filter(AudioJob.id == job_uuid).one_or_none()
        if job is None:
            raise AudioJobFinalizerError(f"Job not found: {job_id}")

        self.assert_success_contract(db=db, job=job, execution=execution)

        runtime_json = self.build_runtime_json(
            execution=execution,
            promotion_reason=promotion_reason,
            provider=provider,
        )

        job.status = "succeeded"
        job.preview_url = execution.preview_url
        job.output_url = execution.output_url
        job.runtime_json = runtime_json
        job.error_code = None
        job.error_message = None
        job.finished_at = datetime.now(UTC)
        job.updated_at = datetime.now(UTC)
        db.commit()
        db.refresh(job)
        return job

    def assert_success_contract(
        self,
        *,
        db: Session,
        job: AudioJob,
        execution: AudioFactoryResult,
    ) -> None:
        if not execution.success:
            raise AudioJobFinalizerError(self._execution_error(execution))

        if not execution.artifacts:
            raise AudioJobFinalizerError("Factory success is invalid: artifacts[] is empty")

        self._assert_validation_passed(execution.validation)
        self._assert_artifact_contracts(execution.artifacts)
        self._assert_db_outputs(db=db, job=job, artifacts=execution.artifacts)

    def build_runtime_json(
        self,
        *,
        execution: AudioFactoryResult,
        promotion_reason: str,
        provider: str,
    ) -> dict:
        artifacts = [artifact.model_dump() for artifact in execution.artifacts]
        return {
            "provider": provider,
            "workflow_type": execution.workflow_type.value,
            "artifact_contract_version": execution.artifact_contract_version,
            "artifacts": artifacts,
            "factory_validation": execution.validation,
            "factory_metrics": execution.metrics,
            "promotion_gate": self._promotion_gate(promotion_reason),
            "preview_url": execution.preview_url,
            "output_url": execution.output_url,
        }

    def _assert_validation_passed(self, validation: dict) -> None:
        file_validation = validation.get("file") or {}
        db_validation = validation.get("db") or {}

        if file_validation.get("passed") is not True:
            raise AudioJobFinalizerError(
                f"Factory file validation did not pass: {file_validation}"
            )

        if db_validation.get("passed") is not True:
            raise AudioJobFinalizerError(
                f"Factory DB validation did not pass: {db_validation}"
            )

    def _assert_artifact_contracts(self, artifacts: list[AudioArtifactContract]) -> None:
        for artifact in artifacts:
            if not artifact.artifact_id:
                raise AudioJobFinalizerError("Artifact is missing artifact_id")
            if not artifact.storage_key:
                raise AudioJobFinalizerError(f"Artifact {artifact.artifact_id} is missing storage_key")
            if not artifact.mime_type:
                raise AudioJobFinalizerError(f"Artifact {artifact.artifact_id} is missing mime_type")
            if not artifact.checksum:
                raise AudioJobFinalizerError(f"Artifact {artifact.artifact_id} is missing checksum")
            if not artifact.size_bytes or artifact.size_bytes <= 0:
                raise AudioJobFinalizerError(f"Artifact {artifact.artifact_id} has invalid size_bytes")
            if artifact.promotion_status not in self.VERIFIED_STATUSES:
                raise AudioJobFinalizerError(
                    f"Artifact {artifact.artifact_id} has invalid promotion_status={artifact.promotion_status}"
                )

    def _assert_db_outputs(
        self,
        *,
        db: Session,
        job: AudioJob,
        artifacts: list[AudioArtifactContract],
    ) -> None:
        rows = db.query(AudioOutput).filter(AudioOutput.job_id == job.id).all()
        rows_by_artifact_id = {
            row.artifact_id: row
            for row in rows
            if row.artifact_id
        }
        rows_by_type = {row.output_type: row for row in rows}

        for artifact in artifacts:
            row = rows_by_artifact_id.get(artifact.artifact_id) or rows_by_type.get(artifact.artifact_type)
            if row is None:
                raise AudioJobFinalizerError(
                    f"Missing audio_outputs row for artifact={artifact.artifact_id} type={artifact.artifact_type}"
                )
            if row.checksum != artifact.checksum:
                raise AudioJobFinalizerError(
                    f"DB checksum mismatch for artifact={artifact.artifact_id}"
                )
            if row.size_bytes != artifact.size_bytes:
                raise AudioJobFinalizerError(
                    f"DB size_bytes mismatch for artifact={artifact.artifact_id}"
                )
            if row.storage_key != artifact.storage_key:
                raise AudioJobFinalizerError(
                    f"DB storage_key mismatch for artifact={artifact.artifact_id}"
                )
            if row.promotion_status not in self.VERIFIED_STATUSES:
                raise AudioJobFinalizerError(
                    f"DB row promotion_status invalid for artifact={artifact.artifact_id}: {row.promotion_status}"
                )

    def _promotion_gate(self, promotion_reason: str) -> dict:
        return {
            "contract_pass": True,
            "lineage_pass": True,
            "write_integrity_pass": True,
            "db_persistence_pass": True,
            "factory_file_validation_pass": True,
            "factory_db_validation_pass": True,
            "replayability_pass": False,
            "determinism_pass": False,
            "drift_budget_pass": False,
            "replayability_status": "pending",
            "determinism_status": "pending",
            "drift_budget_status": "pending",
            "promotion_status": "contract_verified",
            "promotion_reason": promotion_reason,
            "checked_at": datetime.now(UTC).isoformat(),
        }

    def _execution_error(self, execution: AudioFactoryResult) -> str:
        if execution.incident:
            return execution.incident.get("error_message") or str(execution.incident)
        if execution.validation:
            return execution.validation.get("error") or str(execution.validation)
        return "Factory execution failed"
