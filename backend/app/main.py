import os

from fastapi import FastAPI
from app.api.router import api_router


def create_app() -> FastAPI:
    app = FastAPI(title='Audio AI System API', version='0.1.0')

    @app.get('/healthz', tags=['health'])
    async def healthcheck() -> dict[str, str]:
        return {'status': 'ok'}

    app.include_router(api_router, prefix='/api/v1')
    return app


app = create_app()

if os.getenv("BACKEND_SCHEMA_BOOTSTRAP") == "metadata-create-all":
    from app.db.base import Base
    from app.db.session import engine
    import app.models  # noqa: F401 — register all ORM models with Base.metadata
    Base.metadata.create_all(bind=engine)
