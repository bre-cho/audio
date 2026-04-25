from __future__ import annotations

import time
import uuid
from typing import Protocol

from sqlalchemy.orm import Session

from app.audio_factory.artifact_contract import ArtifactContractService
from app.audio_factory.artifact_persistence import ArtifactPersistenceService
from app.audio_factory.artifact_validation import ArtifactValidationService
from app.audio_factory.incident_report import IncidentReportService
from app.audio_factory.metrics_report import MetricsReportService
from app.audio_factory.schemas import AudioFactoryResult, AudioTaskRequest
from app.audio_factory.workflow_router import AudioWorkflowRouter
from app.models.audio_output import AudioOutput


class AudioProviderRuntime(Protocol):
    def run(self, task: AudioTaskRequest, workflow_spec: dict) -> dict:
        raise NotImplementedError


class AudioFactoryExecutor:
    def __init__(
        self,
        *,
        provider_runtime: AudioProviderRuntime,
        router: AudioWorkflowRouter | None = None,
        contract_service: ArtifactContractService | None = None,
        validation_service: ArtifactValidationService | None = None,
        persistence_service: ArtifactPersistenceService | None = None,
        metrics_service: MetricsReportService | None = None,
        incident_service: IncidentReportService | None = None,
    ):
        self.provider_runtime = provider_runtime
        self.router = router or AudioWorkflowRouter()
        self.contract_service = contract_service or ArtifactContractService()
        self.validation_service = validation_service or ArtifactValidationService()
        self.persistence_service = persistence_service or ArtifactPersistenceService()
        self.metrics_service = metrics_service or MetricsReportService()
        self.incident_service = incident_service or IncidentReportService()

    def execute(
        self,
        *,
        db: Session,
        task: AudioTaskRequest,
    ) -> AudioFactoryResult:
        started = time.time()
        job_id = task.source_job_id or str(uuid.uuid4())

        try:
            self.router.validate_task_shape(task)
            workflow_spec = self.router.resolve(task)
            runtime_output = self.provider_runtime.run(task, workflow_spec)
            contracts = self.contract_service.create_contracts(
                task=task,
                source_job_id=job_id,
                runtime_output=runtime_output,
            )
            validation_file = self.validation_service.validate_contracts(contracts=contracts)
            self.persistence_service.persist(db=db, job_id=job_id, contracts=contracts)
            validation_db = self.validation_service.validate_db_persistence(
                db=db,
                output_model=AudioOutput,
                job_id=job_id,
                contracts=contracts,
            )
            metrics = self.metrics_service.build_success_metrics(
                workflow_type=task.workflow_type.value,
                job_id=job_id,
                started_at=started,
                artifacts=contracts,
            )
            return AudioFactoryResult(
                success=True,
                workflow_type=task.workflow_type,
                job_id=job_id,
                artifacts=contracts,
                preview_url=runtime_output.get("preview_url"),
                output_url=runtime_output.get("output_url"),
                artifact_contract_version=runtime_output.get("artifact_contract_version"),
                validation={
                    "file": validation_file,
                    "db": validation_db,
                },
                metrics=metrics,
            )
        except Exception as exc:
            incident = self.incident_service.build_failure_incident(
                workflow_type=task.workflow_type.value,
                job_id=job_id,
                error=exc,
                started_at=started,
            )
            return AudioFactoryResult(
                success=False,
                workflow_type=task.workflow_type,
                job_id=job_id,
                validation={
                    "passed": False,
                    "error": str(exc),
                },
                incident=incident,
                metrics=self.metrics_service.build_failure_metrics(
                    workflow_type=task.workflow_type.value,
                    job_id=job_id,
                    started_at=started,
                    error=exc,
                ),
            )