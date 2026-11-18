import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import mail
from app.database import Base, get_db
from app.main import app

ANA = {"X-Dev-User": "ana@uni.org:interested"}
ORG = {"X-Dev-User": "oscar@upm.es:organizer"}
PART = {"X-Dev-User": "pablo@uni.org:participant"}


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "dev")
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    app.dependency_overrides[get_db] = lambda: session
    mail.outbox.clear()
    yield TestClient(app)
    app.dependency_overrides.clear()
    session.close()


def test_interested_researcher_can_request_and_gets_confirmation(client):
    r = client.post("/api/participation-requests", json={"message": "hi"}, headers=ANA)
    assert r.status_code == 201 and r.json()["status"] == "pending"
    assert [m.to for m in mail.outbox] == ["ana@uni.org"]


def test_visitor_cannot_request(client):
    assert client.post("/api/participation-requests", json={}).status_code == 401


def test_cannot_have_two_open_requests(client):
    client.post("/api/participation-requests", json={}, headers=ANA)
    assert client.post("/api/participation-requests", json={}, headers=ANA).status_code == 409


def test_participants_do_not_need_to_request(client):
    assert client.post("/api/participation-requests", json={}, headers=PART).status_code == 409


def test_only_organizers_list_requests(client):
    client.post("/api/participation-requests", json={}, headers=ANA)
    assert client.get("/api/participation-requests", headers=ANA).status_code == 403
    assert client.get("/api/participation-requests", headers=PART).status_code == 403
    assert client.get("/api/participation-requests").status_code == 401
    rows = client.get("/api/participation-requests", headers=ORG).json()
    assert [r["email"] for r in rows] == ["ana@uni.org"]


def test_researcher_sees_only_their_own_requests(client):
    client.post("/api/participation-requests", json={}, headers=ANA)
    assert len(client.get("/api/participation-requests/mine", headers=ANA).json()) == 1
    other = {"X-Dev-User": "bea@uni.org:interested"}
    assert client.get("/api/participation-requests/mine", headers=other).json() == []


def test_organizer_approves_and_researcher_is_notified(client):
    rid = client.post("/api/participation-requests", json={}, headers=ANA).json()["id"]
    mail.outbox.clear()
    r = client.post(f"/api/participation-requests/{rid}/decision", json={"approve": True}, headers=ORG)
    assert r.status_code == 200
    assert r.json()["status"] == "approved" and r.json()["decided_by"] == "oscar@upm.es"
    assert mail.outbox[0].to == "ana@uni.org" and "approved" in mail.outbox[0].subject


def test_rejected_researcher_can_apply_again(client):
    rid = client.post("/api/participation-requests", json={}, headers=ANA).json()["id"]
    client.post(f"/api/participation-requests/{rid}/decision", json={"approve": False}, headers=ORG)
    assert client.post("/api/participation-requests", json={}, headers=ANA).status_code == 201


def test_decision_is_final_and_restricted(client):
    rid = client.post("/api/participation-requests", json={}, headers=ANA).json()["id"]
    assert client.post(f"/api/participation-requests/{rid}/decision", json={"approve": True}, headers=ANA).status_code == 403
    client.post(f"/api/participation-requests/{rid}/decision", json={"approve": True}, headers=ORG)
    assert client.post(f"/api/participation-requests/{rid}/decision", json={"approve": False}, headers=ORG).status_code == 409
    assert client.post("/api/participation-requests/999/decision", json={"approve": True}, headers=ORG).status_code == 404
