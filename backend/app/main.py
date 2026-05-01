import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import ARTIFACT_ROOT
from app.core.rate_limit import rate_limit


def create_app() -> FastAPI:
    app = FastAPI(title='API He thong AI Am thanh', version='0.1.0')

    # CORS — in production set CORS_ORIGINS to a comma-separated list of
    # allowed origins (e.g. "https://app.example.com").  Defaults to '' which
    # blocks all cross-origin requests so the API is safe out of the box.
    raw_origins = os.getenv("CORS_ORIGINS", "").strip()
    origins = [o.strip() for o in raw_origins.split(",") if o.strip()] if raw_origins else []
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get('/healthz', tags=['health'])
    async def healthcheck() -> dict[str, str]:
        return {'status': 'ok'}

    app.include_router(api_router, prefix='/api/v1')

    # Serve artifact files (audio previews and outputs)
    Path(ARTIFACT_ROOT).mkdir(parents=True, exist_ok=True)
    app.mount('/artifacts', StaticFiles(directory=ARTIFACT_ROOT), name='artifacts')

    return app


app = create_app()

bootstrap_mode = os.getenv("BACKEND_SCHEMA_BOOTSTRAP")

if bootstrap_mode in {"metadata-create-all", "audio-factory-migrate"}:
    from app.db.base import Base
    from app.db.session import engine
    from app import models as _models  # noqa: F401 — register ORM models without shadowing `app`

    Base.metadata.create_all(bind=engine)

    if bootstrap_mode == "audio-factory-migrate":
        import subprocess
        import sys
        from pathlib import Path

        _alembic_ini = Path(__file__).resolve().parents[1] / "alembic.ini"
        subprocess.run(
            [sys.executable, "-m", "alembic", "-c", str(_alembic_ini), "upgrade", "head"],
            cwd=str(Path(__file__).resolve().parents[1]),
            check=True,
        )
