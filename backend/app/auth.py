"""Roles and access control.

The portal delegates authentication to Amazon Cognito (decision D6). Until that
integration exists, a TEMPORARY development mode identifies the user from the
``X-Dev-User`` header (``email:role``). It is enabled only with ``AUTH_MODE=dev``
and must never be enabled in a deployed environment.

Only ``current_user`` knows how the user is identified. When Cognito is added, it
will validate the token there; endpoints and role checks do not change.
"""
import os
from dataclasses import dataclass
from enum import IntEnum

from fastapi import Depends, HTTPException, Request


class Role(IntEnum):
    """Roles of an authenticated user, ordered by privilege.

    Visitors (the *researcher* concept) are not authenticated and have no role.
    """

    INTERESTED = 1  # any authenticated user (c-interested-researcher)
    PARTICIPANT = 2  # validated by an organizer (c-participant-researcher)
    ORGANIZER = 3  # UPM and ESPE researchers (c-organizer)


@dataclass(frozen=True)
class User:
    email: str
    role: Role


def _dev_user(request: Request) -> User | None:
    raw = request.headers.get("X-Dev-User")
    if not raw or ":" not in raw:
        return None
    email, _, role = raw.rpartition(":")
    try:
        return User(email=email.strip(), role=Role[role.strip().upper()])
    except KeyError:
        return None


def current_user(request: Request) -> User | None:
    """The authenticated user, or None for a visitor."""
    if os.getenv("AUTH_MODE", "off") == "dev":
        return _dev_user(request)
    return None


def require_role(minimum: Role):
    """Dependency that allows only users with at least the given role."""

    def checker(user: User | None = Depends(current_user)) -> User:
        if user is None:
            raise HTTPException(status_code=401, detail="Authentication required")
        if user.role < minimum:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return user

    return checker
