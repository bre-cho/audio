from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401 — register all ORM models with Base.metadata
from app.api.deps import get_db
from app.core.config import settings
from app.db.base import Base
from app.main import create_app


@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def db_session(db_engine):
    TestingSessionLocal = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    application = create_app()
    application.dependency_overrides[get_db] = lambda: db_session
    # Celery tasks are mocked so tests do not require a running broker
    with (
        patch("app.workers.audio_tasks.process_tts_job.delay"),
        patch("app.workers.audio_tasks.process_batch_job.delay"),
        patch("app.workers.audio_tasks.process_conversation_job.delay"),
    ):
        with TestClient(application) as c:
            yield c
    application.dependency_overrides.clear()
