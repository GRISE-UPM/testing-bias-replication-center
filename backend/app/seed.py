"""Loads SAMPLE data for local development. The values are placeholders, not real project data.

Usage:  python -m app.seed
"""
from .database import Base, SessionLocal, engine
from .models import Replication

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
            print("Database already has data; nothing loaded.")
