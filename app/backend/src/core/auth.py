from __future__ import annotations

from dataclasses import dataclass
from fastapi import Depends, Header, HTTPException, status


@dataclass(frozen=True)
class CurrentUser:
    id: int
    role: str  # "admin" | "user"


async def get_current_user(
    x_user_id: int | None = Header(default=None, alias="X-User-Id"),
    x_user_role: str | None = Header(default=None, alias="X-User-Role"),
) -> CurrentUser:
    # OAuth-заглушка: берём пользователя из заголовков (для e2e-тестов)
    user_id = x_user_id or 1
    role = (x_user_role or "user").lower()
    if role not in {"admin", "user"}:
        role = "user"
    return CurrentUser(id=int(user_id), role=role)


def require_admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin_only")
    return user


