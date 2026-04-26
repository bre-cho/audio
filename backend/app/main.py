import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import ARTIFACT_ROOT


def create_app() -> FastAPI:
    app = FastAPI(title='API He thong AI Am thanh', version='0.1.0')

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

        _alembic_ini = Path(__file__).resolve().parents[2] / "alembic.ini"
        subprocess.run(
            [sys.executable, "-m", "alembic", "-c", str(_alembic_ini), "upgrade", "head"],
            cwd=str(Path(__file__).resolve().parents[2]),
            check=True,
        )
