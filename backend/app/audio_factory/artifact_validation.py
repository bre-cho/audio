from __future__ import annotations

from pathlib import Path
from uuid import UUID

from sqlalchemy.orm import Session

from app.audio_factory.schemas import AudioArtifactContract
from app.core.runtime_guard import is_production_like
from app.core.storage import compute_sha256


class ArtifactValidationError(RuntimeError):
    pass


class ArtifactValidationService:
    def validate_contracts(self, *, contracts: list[AudioArtifactContract]) -> dict:
        summaries: list[dict] = []

        for contract in contracts:
            path = Path(contract.path or "")
            checks = {
                "file_exists": path.exists(),
                "size_gt_zero": contract.size_bytes > 0,
                "mime_type_present": bool(contract.mime_type),
                "storage_key_present": bool(contract.storage_key),
                "checksum_present": bool(contract.checksum),
                "size_match": False,
                "checksum_match": False,
            }

            if not checks["file_exists"]:
                raise ArtifactValidationError(f"Artifact file missing: {contract.path}")

            actual_size = path.stat().st_size
            checks["size_match"] = actual_size == contract.size_bytes
            checks["checksum_match"] = compute_sha256(path.read_bytes()) == contract.checksum

            failed = [name for name, passed in checks.items() if not passed]
            if failed:
                raise ArtifactValidationError(
                    f"Artifact validation failed for {contract.artifact_type}: {failed}"
                )

            if contract.promotion_status != "blocked":
                if is_production_like() and (
                    contract.generation_mode != "real"
                    or contract.audio_contains_signal is not True
                    or contract.provider_verified is not True
                ):
                    contract.promotion_status = "blocked"
                    contract.promotion_reason = "artifact failed strict runtime truth gates"
                else:
                    contract.promotion_status = "contract_verified"
            summaries.append(
                {
                    "artifact_id": contract.artifact_id,
                    "artifact_type": contract.artifact_type,
                    "checks": checks,
                    "promotion_status": contract.promotion_status,
                }
            )

        return {
            "passed": True,
            "artifacts": summaries,
        }

    def validate_db_persistence(
        self,
        *,
        db: Session,
        output_model,
        job_id: str,
        contracts: list[AudioArtifactContract],
    ) -> dict:
        rows = db.query(output_model).filter(output_model.job_id == UUID(job_id)).all()
        rows_by_artifact_id = {
            getattr(row, "artifact_id", None): row
            for row in rows
            if getattr(row, "artifact_id", None)
        }
        rows_by_type = {row.output_type: row for row in rows}
        summaries: list[dict] = []

        for contract in contracts:
            row = rows_by_artifact_id.get(contract.artifact_id) or rows_by_type.get(contract.artifact_type)
            checks = {
                "db_row_exists": row is not None,
                "checksum_match": bool(row and row.checksum == contract.checksum),
                "size_match": bool(row and row.size_bytes == contract.size_bytes),
                "promotion_status_verified": bool(
                    row and getattr(row, "promotion_status", None) in {"contract_verified", "persisted"}
                ),
            }

            failed = [name for name, passed in checks.items() if not passed]
            if failed:
                raise ArtifactValidationError(
                    f"DB artifact validation failed for {contract.artifact_type}: {failed}"
                )

            summaries.append(
                {
                    "artifact_id": contract.artifact_id,
                    "artifact_type": contract.artifact_type,
                    "checks": checks,
                }
            )

        return {
            "passed": True,
            "artifacts": summaries,
        }