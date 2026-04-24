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
