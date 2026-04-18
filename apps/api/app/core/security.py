from datetime import UTC, datetime

import jwt
from fastapi import HTTPException, status

from app.core.config import settings


class TokenPayloadError(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def decode_token(token: str) -> dict:
    demo_tokens = {
        settings.demo_operator_token: {"sub": "demo-operator", "role": "operator"},
        settings.demo_approver_token: {"sub": "demo-approver", "role": "approver"},
        settings.demo_admin_token: {"sub": "demo-admin", "role": "admin"},
    }
    if token in demo_tokens and token is not None:
        return demo_tokens[token]

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
            options={"require": ["exp", "sub", "role"]},
        )
    except jwt.PyJWTError as exc:
        raise TokenPayloadError() from exc

    exp = payload.get("exp")
    if isinstance(exp, int):
        if datetime.fromtimestamp(exp, tz=UTC) < datetime.now(tz=UTC):
            raise TokenPayloadError()
    return payload
