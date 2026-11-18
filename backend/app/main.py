import os

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from . import models
from .auth import Role, User, require_role
from .database import Base, engine, get_db
from .schemas import MeResponse, PublicStats

app = FastAPI(title="Replication Center API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:4200").split(","),
    allow_methods=["GET"],
    allow_headers=["*"],
)

Base.metadata.create_all(engine)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/stats", response_model=PublicStats)
def public_stats(db: Session = Depends(get_db)) -> PublicStats:
    """Public figures for the landing page. No authentication required (#3)."""
    r = models.Replication
    experiments, subjects, institutions = db.execute(
        select(
            func.count(r.id),
            func.coalesce(func.sum(r.subjects), 0),
            func.count(distinct(r.institution)),
        )
    ).one()
    return PublicStats(experiments=experiments, subjects=subjects, institutions=institutions)


@app.get("/api/me", response_model=MeResponse)
def me(user: User = Depends(require_role(Role.INTERESTED))) -> MeResponse:
    """Identity and role of the current user. Requires authentication."""
    return MeResponse(email=user.email, role=user.role.name.lower())
