import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.auth import Role, User, require_role
from app.main import app as main_app


@pytest.fixture()
def dev_mode(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "dev")


def hdr(email, role):
    return {"X-Dev-User": f"{email}:{role}"}


def test_me_requires_authentication(dev_mode):
    assert TestClient(main_app).get("/api/me").status_code == 401


def test_me_returns_identity_and_role(dev_mode):
    r = TestClient(main_app).get("/api/me", headers=hdr("a@b.org", "organizer"))
    assert r.status_code == 200
    assert r.json() == {"email": "a@b.org", "role": "organizer"}


def test_unknown_role_is_treated_as_visitor(dev_mode):
    assert TestClient(main_app).get("/api/me", headers=hdr("a@b.org", "admin")).status_code == 401


def test_malformed_header_is_treated_as_visitor(dev_mode):
    r = TestClient(main_app).get("/api/me", headers={"X-Dev-User": "nonsense"})
    assert r.status_code == 401


def test_dev_header_is_ignored_when_dev_mode_is_off(monkeypatch):
    monkeypatch.delenv("AUTH_MODE", raising=False)
    r = TestClient(main_app).get("/api/me", headers=hdr("a@b.org", "organizer"))
    assert r.status_code == 401


def test_dev_header_is_ignored_in_any_other_mode(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "cognito")
    assert TestClient(main_app).get("/api/me", headers=hdr("a@b.org", "organizer")).status_code == 401


def _app_with(minimum):
    app = FastAPI()

    @app.get("/x")
    def x(user: User = Depends(require_role(minimum))):
        return {"ok": True}

    return TestClient(app)


@pytest.mark.parametrize(
    "have,need,status",
    [
        ("interested", Role.INTERESTED, 200),
        ("participant", Role.INTERESTED, 200),
        ("organizer", Role.PARTICIPANT, 200),
        ("interested", Role.PARTICIPANT, 403),
        ("participant", Role.ORGANIZER, 403),
    ],
)
def test_role_hierarchy(dev_mode, have, need, status):
    assert _app_with(need).get("/x", headers=hdr("a@b.org", have)).status_code == status


def test_visitor_gets_401_on_protected_route(dev_mode):
    assert _app_with(Role.INTERESTED).get("/x").status_code == 401
