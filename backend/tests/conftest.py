from __future__ import annotations

import subprocess
import sys
from pathlib import Path
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
from app.models.audio_output import AudioOutput

_BACKEND_DIR = Path(__file__).resolve().parents[1]
_ALEMBIC_INI = _BACKEND_DIR / "alembic.ini"


@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 3},
    )
    AudioOutput.__table__.drop(bind=engine, checkfirst=True)
    Base.metadata.create_all(bind=engine)
    subprocess.run(
        [sys.executable, "-m", "alembic", "-c", str(_ALEMBIC_INI), "upgrade", "head"],
        cwd=str(_BACKEND_DIR),
        check=True,
    )
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
        patch("app.workers.clone_tasks.process_clone_job.delay"),
        patch("app.workers.clone_tasks.process_clone_preview_job.delay"),
    ):
        with TestClient(application) as c:
            yield c
    application.dependency_overrides.clear()
