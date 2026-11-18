import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import mail
from app.database import Base, get_db
from app.main import app
from app.models import Demo, ExperimentDetails, Paper

H = {"X-Dev-User": "ana@uni.org:interested"}


@pytest.fixture()
def db(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "dev")
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    app.dependency_overrides[get_db] = lambda: session
    mail.outbox.clear()
    yield session
    app.dependency_overrides.clear()
    session.close()


def publish(db):
    db.add(ExperimentDetails(title="T", summary="S", description="D"))
    db.add_all(
        [
            Paper(title="Old", authors="A", venue="V", year=2024, url="u1"),
            Paper(title="New", authors="B", venue="V", year=2026, url="u2"),
        ]
    )
    db.add(Demo(title="Demo", url="u3"))
    db.commit()


def test_visitor_cannot_see_details(db):
    publish(db)
    assert TestClient(app).get("/api/experiment").status_code == 401


def test_interested_researcher_sees_details_with_newest_paper_first(db):
    publish(db)
    r = TestClient(app).get("/api/experiment", headers=H)
    assert r.status_code == 200
    body = r.json()
    assert body["title"] == "T"
    assert [p["title"] for p in body["papers"]] == ["New", "Old"]
    assert body["demos"] == [{"title": "Demo", "url": "u3"}]


def test_response_has_no_code_data_or_repository_fields(db):
    publish(db)
    body = TestClient(app).get("/api/experiment", headers=H).json()
    assert set(body) == {"title", "summary", "description", "papers", "demos"}


def test_404_when_not_published(db):
    assert TestClient(app).get("/api/experiment", headers=H).status_code == 404


def test_email_goes_to_the_users_own_address(db):
    publish(db)
    r = TestClient(app).post("/api/experiment/email", headers=H)
    assert r.status_code == 202
    assert len(mail.outbox) == 1
    msg = mail.outbox[0]
    assert msg.to == "ana@uni.org"
    assert "New" in msg.body and "Demo" in msg.body


def test_visitor_cannot_request_email(db):
    publish(db)
    assert TestClient(app).post("/api/experiment/email").status_code == 401
    assert mail.outbox == []
