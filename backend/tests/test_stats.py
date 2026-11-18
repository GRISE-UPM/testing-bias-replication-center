import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Replication


@pytest.fixture()
def session():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    app.dependency_overrides[get_db] = lambda: db
    yield db
    app.dependency_overrides.clear()
    db.close()


def test_stats_empty(session):
    r = TestClient(app).get("/api/stats")
    assert r.status_code == 200
    assert r.json() == {"experiments": 0, "subjects": 0, "institutions": 0}


def test_stats_counts_each_figure(session):
    session.add_all(
        [
            Replication(title="R1", institution="A", subjects=10),
            Replication(title="R2", institution="A", subjects=5),
            Replication(title="R3", institution="B", subjects=7),
        ]
    )
    session.commit()
    r = TestClient(app).get("/api/stats")
    assert r.json() == {"experiments": 3, "subjects": 22, "institutions": 2}


def test_stats_needs_no_authentication(session):
    assert TestClient(app).get("/api/stats").status_code == 200


def test_stats_exposes_only_the_three_figures(session):
    session.add(Replication(title="R1", institution="A", subjects=1))
    session.commit()
    assert set(TestClient(app).get("/api/stats").json()) == {"experiments", "subjects", "institutions"}
