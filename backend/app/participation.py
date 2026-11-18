"""Requests to join the project (#7) and their validation by organizers (#4, nfr-participation)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import mail, models
from .auth import Role, User, require_role
from .database import get_db
from .schemas import DecisionIn, JoinRequestIn, JoinRequestOut

router = APIRouter(prefix="/api/participation-requests", tags=["participation"])


def _out(r: models.ParticipationRequest) -> JoinRequestOut:
    return JoinRequestOut(id=r.id, email=r.email, message=r.message, status=r.status, decided_by=r.decided_by)


@router.post("", response_model=JoinRequestOut, status_code=201)
def create(
    body: JoinRequestIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(Role.INTERESTED)),
):
    """An interested researcher asks to join. One open or approved request per person."""
    if user.role >= Role.PARTICIPANT:
        raise HTTPException(409, "You already take part in the project")
    existing = db.scalars(
        select(models.ParticipationRequest).where(
            models.ParticipationRequest.email == user.email,
            models.ParticipationRequest.status.in_(["pending", "approved"]),
        )
    ).first()
    if existing:
        raise HTTPException(409, f"You already have a {existing.status} request")
    req = models.ParticipationRequest(email=user.email, message=body.message)
    db.add(req)
    db.commit()
    db.refresh(req)
    mail.send_email(
        user.email,
        "Replication Center: request received",
        "We received your request to join the project. An organizer will review it.",
    )
    return _out(req)


@router.get("/mine", response_model=list[JoinRequestOut])
def mine(db: Session = Depends(get_db), user: User = Depends(require_role(Role.INTERESTED))):
    rows = db.scalars(
        select(models.ParticipationRequest)
        .where(models.ParticipationRequest.email == user.email)
        .order_by(models.ParticipationRequest.id.desc())
    ).all()
    return [_out(r) for r in rows]


@router.get("", response_model=list[JoinRequestOut])
def list_requests(
    status: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(Role.ORGANIZER)),
):
    q = select(models.ParticipationRequest).order_by(models.ParticipationRequest.id)
    if status:
        q = q.where(models.ParticipationRequest.status == status)
    return [_out(r) for r in db.scalars(q).all()]


@router.post("/{request_id}/decision", response_model=JoinRequestOut)
def decide(
    request_id: int,
    body: DecisionIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(Role.ORGANIZER)),
):
    """An organizer approves or rejects a pending request; the researcher is notified by email."""
    req = db.get(models.ParticipationRequest, request_id)
    if req is None:
        raise HTTPException(404, "Request not found")
    if req.status != "pending":
        raise HTTPException(409, "This request was already decided")
    req.status = "approved" if body.approve else "rejected"
    req.decided_by = user.email
    db.commit()
    mail.send_email(
        req.email,
        "Replication Center: your request was " + req.status,
        "Your request to join the project was " + req.status + ".",
    )
    return _out(req)
