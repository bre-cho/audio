from collections.abc import Generator
from uuid import UUID
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from pydantic import BaseModel, Field

from app.core.config import settings
from app.db.session import SessionLocal


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


bearer_scheme = HTTPBearer(auto_error=False)


class AuthContext(BaseModel):
    user_id: UUID
    token_type: str = 'anonymous'
    roles: list[str] = Field(default_factory=list)
    scopes: list[str] = Field(default_factory=list)


def _normalize_list_claim(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [part for part in value.replace(',', ' ').split() if part]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _parse_api_token_entry(entry: str) -> tuple[str, UUID, list[str], list[str]] | None:
    # Supported shapes:
    # - token
    # - token:user_uuid
    # - token:user_uuid:scope1|scope2
    # - token:user_uuid:scope1|scope2:role1|role2
    parts = [part.strip() for part in entry.split(':')]
    if not parts or not parts[0]:
        return None

    token = parts[0]
    user_id = UUID(settings.default_user_id)
    scopes: list[str] = []
    roles: list[str] = []

    if len(parts) >= 2 and parts[1]:
        try:
            user_id = UUID(parts[1])
        except ValueError:
            return None
    if len(parts) >= 3 and parts[2]:
        scopes = [item for item in parts[2].split('|') if item]
    if len(parts) >= 4 and parts[3]:
        roles = [item for item in parts[3].split('|') if item]

    return token, user_id, scopes, roles


def get_auth_context(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthContext:
    if not settings.auth_enabled:
        return AuthContext(user_id=UUID(settings.default_user_id), token_type='dev-default')

    if not credentials or credentials.scheme.lower() != 'bearer':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Missing bearer token')

    token = credentials.credentials.strip()

    # Preferred production mode: JWT carries user identity + roles/scopes in claims.
    if settings.jwt_secret_key:
        if (
            settings.app_env.lower() in {'prod', 'production'}
            and settings.jwt_algorithm.upper().startswith('HS')
            and len(settings.jwt_secret_key) < 32
        ):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='JWT secret key must be at least 32 chars in production for HS* algorithms',
            )

        try:
            decode_options: dict[str, Any] = {
                'algorithms': [settings.jwt_algorithm],
            }
            if settings.jwt_audience:
                decode_options['audience'] = settings.jwt_audience
            if settings.jwt_issuer:
                decode_options['issuer'] = settings.jwt_issuer

            payload = jwt.decode(token, settings.jwt_secret_key, **decode_options)
            user_claim = payload.get('sub') or payload.get('user_id')
            if not user_claim:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='JWT missing sub/user_id claim',
                )
            return AuthContext(
                user_id=UUID(str(user_claim)),
                token_type='jwt',
                scopes=_normalize_list_claim(payload.get('scopes') or payload.get('scope')),
                roles=_normalize_list_claim(payload.get('roles') or payload.get('role')),
            )
        except jwt.InvalidTokenError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Invalid JWT token: {exc}')
        except ValueError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='JWT user claim is not a valid UUID')

    allowed = {
        item.strip()
        for item in (settings.api_auth_tokens or '').split(',')
        if item.strip()
    }
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Auth is enabled but neither JWT_SECRET_KEY nor API_AUTH_TOKENS is configured',
        )

    token_map: dict[str, AuthContext] = {}
    for item in allowed:
        parsed = _parse_api_token_entry(item)
        if not parsed:
            continue
        parsed_token, user_id, scopes, roles = parsed
        token_map[parsed_token] = AuthContext(
            user_id=user_id,
            token_type='api-token',
            scopes=scopes,
            roles=roles,
        )

    if token not in token_map:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid bearer token')
    return token_map[token]


def get_current_user_id(
    ctx: AuthContext = Depends(get_auth_context),
) -> UUID:
    return ctx.user_id


def require_scopes(*required_scopes: str):
    def _dependency(ctx: AuthContext = Depends(get_auth_context)) -> AuthContext:
        if not required_scopes:
            return ctx

        if 'admin' in ctx.roles:
            return ctx

        available = set(ctx.scopes)
        missing = [scope for scope in required_scopes if scope not in available]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f'Missing required scopes: {", ".join(missing)}',
            )
        return ctx

    return _dependency
