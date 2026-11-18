"""Loads SAMPLE data for local development. The values are placeholders, not real project data.

Usage:  python -m app.seed
"""
from .database import Base, SessionLocal, engine
from .models import Demo, ExperimentDetails, Paper, Replication

SAMPLE = [
    ("Sample replication 1", "Institution A", 30),
    ("Sample replication 2", "Institution B", 24),
    ("Sample replication 3", "Institution C", 18),
]

if __name__ == "__main__":
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if db.query(Replication).count() == 0:
            db.add_all(Replication(title=t, institution=i, subjects=s) for t, i, s in SAMPLE)
            db.commit()
            print(f"Loaded {len(SAMPLE)} sample replications.")
        else:
            print("Replications already loaded.")
        if db.query(ExperimentDetails).count() == 0:
            db.add(
                ExperimentDetails(
                    title="SAMPLE experiment title",
                    summary="Sample summary: replace with the real description of the experiment.",
                    description="Sample description. This placeholder text is not real project content.",
                )
            )
            db.add(Paper(title="Sample paper", authors="A. Author", venue="Sample venue", year=2026, url="https://example.org/paper"))
            db.add(Demo(title="Sample demo", url="https://example.org/demo"))
            db.commit()
            print("Loaded sample experiment details.")
