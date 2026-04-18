from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from app.core.security import decode_token


class AuthenticatedUser(dict):
    @property
    def role(self) -> str:
        return str(self.get("role", ""))


def get_current_user(authorization: Annotated[str | None, Header()] = None) -> AuthenticatedUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.replace("Bearer ", "", 1).strip()
    payload = decode_token(token)
    return AuthenticatedUser(payload)


def require_roles(*allowed_roles: str):
    def dependency(user: Annotated[AuthenticatedUser, Depends(get_current_user)]) -> AuthenticatedUser:
        if user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return user

    return dependency
