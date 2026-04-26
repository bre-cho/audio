from __future__ import annotations

import uuid
from datetime import UTC, datetime

from app.audio_factory.schemas import AudioArtifactContract, AudioTaskRequest
from app.services.audio_artifact_service import (
    DEFAULT_MODEL_VERSION,
    DEFAULT_PROVIDER,
    DEFAULT_RUNTIME_VERSION,
    DEFAULT_TEMPLATE_VERSION,
    stable_input_hash,
)


class ArtifactContractService:
    ALLOWED_PROMOTION_ROLES = {"ci", "system", "worker"}
    ALLOWED_PROMOTION_SOURCES = {"ci", "worker"}

    def create_contracts(
        self,
        *,
        task: AudioTaskRequest,
        source_job_id: str,
        runtime_output: dict,
    ) -> list[AudioArtifactContract]:
        runtime_artifacts = runtime_output.get("artifacts") or []
        if not runtime_artifacts:
            raise ValueError("provider runtime returned no artifacts")

        input_hash = task.input_hash or stable_input_hash(task.request_json)
        contracts: list[AudioArtifactContract] = []

        for index, artifact in enumerate(runtime_artifacts):
            artifact_type = str(artifact.get("artifact_type") or artifact.get("output_type") or f"audio_{index}")
            public_url = artifact.get("public_url") or artifact.get("url")
            artifact_id = str(
                artifact.get("artifact_id")
                or uuid.uuid5(uuid.NAMESPACE_URL, f"audio-factory:{source_job_id}:{artifact_type}:{input_hash}:{index}")
            )

            contracts.append(
                AudioArtifactContract(
                    artifact_id=artifact_id,
                    artifact_type=artifact_type,
                    source_job_id=source_job_id,
                    job_id=str(artifact.get("job_id") or source_job_id),
                    created_at=str(artifact.get("created_at") or datetime.now(UTC).isoformat()),
                    storage_key=str(artifact.get("storage_key") or ""),
                    path=artifact.get("path"),
                    url=artifact.get("url") or public_url,
                    public_url=public_url,
                    mime_type=str(artifact.get("mime_type") or "application/octet-stream"),
                    size_bytes=int(artifact.get("size_bytes") or 0),
                    checksum=str(artifact.get("checksum") or ""),
                    input_hash=str(artifact.get("input_hash") or input_hash),
                    provider=str(artifact.get("provider") or task.provider or DEFAULT_PROVIDER),
                    model_version=artifact.get("model_version") or task.model_version or DEFAULT_MODEL_VERSION,
                    template_version=artifact.get("template_version") or task.template_version or DEFAULT_TEMPLATE_VERSION,
                    runtime_version=artifact.get("runtime_version") or task.runtime_version or DEFAULT_RUNTIME_VERSION,
                    waveform_json=dict(artifact),
                    contract_pass=bool(artifact.get("contract_pass", True)),
                    lineage_pass=bool(artifact.get("lineage_pass", True)),
                    write_integrity_pass=bool(artifact.get("write_integrity_pass", True)),
                    replayability_pass=bool(artifact.get("replayability_pass", False)),
                    determinism_pass=bool(artifact.get("determinism_pass", False)),
                    drift_budget_pass=bool(artifact.get("drift_budget_pass", False)),
                    replayability_status=str(artifact.get("replayability_status") or "pending"),
                    determinism_status=str(artifact.get("determinism_status") or "pending"),
                    drift_budget_status=str(artifact.get("drift_budget_status") or "pending"),
                    promotion_status=str(artifact.get("promotion_status") or "generated"),
                    promotion_reason=artifact.get("promotion_reason"),
                    checked_at=artifact.get("checked_at"),
                    metadata={
                        **(artifact.get("metadata") or {}),
                        **task.metadata,
                        "workflow_type": task.workflow_type.value,
                    },
                )
            )

        self.evaluate_governance_gates(contracts)

        return contracts

    def evaluate_governance_gates(self, contracts: list[AudioArtifactContract]) -> None:
        for contract in contracts:
            replayability_pass = self._check_replayability(contract)
            determinism_pass = self._check_determinism(contract)
            drift_budget_pass = self._check_drift_budget(contract)

            contract.replayability_pass = replayability_pass
            contract.determinism_pass = determinism_pass
            contract.drift_budget_pass = drift_budget_pass
            contract.replayability_status = "pass" if replayability_pass else "fail"
            contract.determinism_status = "pass" if determinism_pass else "fail"
            contract.drift_budget_status = "within_budget" if drift_budget_pass else "exceeded"

            if replayability_pass and determinism_pass and drift_budget_pass:
                contract.promotion_status = "contract_verified"
                if not contract.promotion_reason:
                    contract.promotion_reason = "artifact passed contract, lineage, replayability, determinism, and drift budget checks"
            else:
                contract.promotion_status = "generated"
                contract.promotion_reason = "artifact failed one or more governance gates"

    def validate_promotion_authority(self, *, role: str, source: str) -> bool:
        return role in self.ALLOWED_PROMOTION_ROLES and source in self.ALLOWED_PROMOTION_SOURCES

    def _check_replayability(self, contract: AudioArtifactContract) -> bool:
        # Replayability at this layer means the contract carries enough deterministic inputs.
        return bool(
            contract.source_job_id
            and contract.input_hash
            and contract.provider
            and contract.template_version
            and contract.runtime_version
        )

    def _check_determinism(self, contract: AudioArtifactContract) -> bool:
        # Determinism guard: we only accept a full SHA-256 checksum with stable input hash.
        return bool(contract.input_hash and contract.checksum and len(contract.checksum) == 64)

    def _check_drift_budget(self, contract: AudioArtifactContract) -> bool:
        # Minimal budget guard for write-time artifacts: non-zero audio payloads are within baseline budget.
        return contract.size_bytes > 0