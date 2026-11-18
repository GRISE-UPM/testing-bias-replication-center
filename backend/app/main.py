import os

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from . import mail, models
from .auth import Role, User, require_role
from .database import Base, engine, get_db
from .participation import router as participation_router
from .schemas import ExperimentOut, MeResponse, PublicStats

app = FastAPI(title="Replication Center API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:4200").split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

Base.metadata.create_all(engine)
app.include_router(participation_router)


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


def _experiment(db: Session) -> ExperimentOut:
    details = db.scalars(select(models.ExperimentDetails)).first()
    if details is None:
        raise HTTPException(status_code=404, detail="Experiment details not published yet")
    papers = db.scalars(select(models.Paper).order_by(models.Paper.year.desc(), models.Paper.id)).all()
    demos = db.scalars(select(models.Demo).order_by(models.Demo.id)).all()
    return ExperimentOut(
        title=details.title,
        summary=details.summary,
        description=details.description,
        papers=[
            {"title": p.title, "authors": p.authors, "venue": p.venue, "year": p.year, "url": p.url}
            for p in papers
        ],
        demos=[{"title": d.title, "url": d.url} for d in demos],
    )


@app.get("/api/experiment", response_model=ExperimentOut)
def experiment(
    db: Session = Depends(get_db), user: User = Depends(require_role(Role.INTERESTED))
) -> ExperimentOut:
    """Experiment details for authenticated researchers (#1)."""
    return _experiment(db)


@app.post("/api/experiment/email", status_code=202)
def email_experiment(
    db: Session = Depends(get_db), user: User = Depends(require_role(Role.INTERESTED))
):
    """Sends the same information to the email associated with the user's identity (#1)."""
    e = _experiment(db)
    lines = [e.title, "", e.summary, "", e.description, "", "Papers:"]
    lines += [f"- {p.title} ({p.authors}, {p.venue}, {p.year}) {p.url}" for p in e.papers]
    lines += ["", "Demos:"] + [f"- {d.title} {d.url}" for d in e.demos]
    mail.send_email(user.email, f"Replication Center: {e.title}", "\n".join(lines))
    return {"status": "queued"}
