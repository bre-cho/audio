# Backend Skeleton Merge Notes

## Immediate wiring steps
1. Register `app = create_app()` in your existing ASGI entrypoint.
2. Replace placeholder `default_user_id` logic with your real auth/user context.
3. Point `database_url` to your real Postgres DSN.
4. Replace provider stubs with real API adapters.
5. Add Alembic migration files for the included models.

## Important placeholders
- upload route is placeholder only
- Celery tasks only enqueue/echo
- no real storage writes yet
- no auth or RBAC yet
- no rate limiting yet
