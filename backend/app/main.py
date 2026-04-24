import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import ARTIFACT_ROOT


def create_app() -> FastAPI:
    app = FastAPI(title='Audio AI System API', version='0.1.0')

    @app.get('/healthz', tags=['health'])
    async def healthcheck() -> dict[str, str]:
        return {'status': 'ok'}

    app.include_router(api_router, prefix='/api/v1')

    # Serve artifact files (audio previews and outputs)
    Path(ARTIFACT_ROOT).mkdir(parents=True, exist_ok=True)
    app.mount('/artifacts', StaticFiles(directory=ARTIFACT_ROOT), name='artifacts')

    return app


app = create_app()

if os.getenv("BACKEND_SCHEMA_BOOTSTRAP") == "metadata-create-all":
    from app.db.base import Base
    from app.db.session import engine
    import app.models  # noqa: F401 — register all ORM models with Base.metadata
    Base.metadata.create_all(bind=engine)
