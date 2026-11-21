"""Roles and access control.

The portal delegates authentication to Amazon Cognito (decision D6).

``AUTH_MODE`` selects how the user is identified:

* ``cognito``: the ``Authorization: Bearer`` Access Token is validated (see ``cognito.py``).
  Role: group ``organizer`` -> ORGANIZER; group ``participant`` or an approved
  participation request -> PARTICIPANT; any other signed-in user -> INTERESTED.
* ``dev``: development only, the ``X-Dev-User`` header (``email:role``) is trusted.
  It must never be enabled in a deployed environment.
* anything else (default): nobody is authenticated.

Only ``current_user`` knows how the user is identified; endpoints and role checks
do not change.
"""
import os
from dataclasses import dataclass
from enum import IntEnum

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import cognito, models
from .database import get_db


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


def _bearer_token(request: Request) -> str | None:
    scheme, _, token = request.headers.get("Authorization", "").partition(" ")
    return token.strip() if scheme.lower() == "bearer" and token.strip() else None


def _cognito_user(request: Request, db: Session) -> User | None:
    token = _bearer_token(request)
    if token is None:
        return None
    try:
        claims = cognito.verify_access_token(token)
        email = cognito.email_for(token, claims["sub"])
    except cognito.CognitoError:
        return None
    groups = set(claims.get("cognito:groups", []))
    if "organizer" in groups:
        role = Role.ORGANIZER
    elif "participant" in groups or _has_approved_request(db, email):
        role = Role.PARTICIPANT
    else:
        role = Role.INTERESTED
    return User(email=email, role=role)


def _has_approved_request(db: Session, email: str) -> bool:
    return (
        db.scalars(
            select(models.ParticipationRequest).where(
                models.ParticipationRequest.email == email,
                models.ParticipationRequest.status == "approved",
            )
        ).first()
        is not None
    )


def current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    """The authenticated user, or None for a visitor."""
    mode = os.getenv("AUTH_MODE", "off")
    if mode == "dev":
        return _dev_user(request)
    if mode == "cognito":
        return _cognito_user(request, db)
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
