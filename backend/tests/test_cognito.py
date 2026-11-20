"""Cognito token validation and role mapping. No AWS access is needed: tokens are signed
with a throw-away RSA key and the module's key lookup is replaced."""
import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import cognito, models
from app.database import Base, get_db
from app.main import app

REGION, POOL, CLIENT = "us-east-1", "us-east-1_TEST", "client123"
ISSUER = f"https://cognito-idp.{REGION}.amazonaws.com/{POOL}"
KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
OTHER_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture(autouse=True)
def cognito_mode(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "cognito")
    monkeypatch.setenv("COGNITO_REGION", REGION)
    monkeypatch.setenv("COGNITO_USER_POOL_ID", POOL)
    monkeypatch.setenv("COGNITO_CLIENT_ID", CLIENT)
    monkeypatch.setenv("COGNITO_DOMAIN", "https://example.auth.us-east-1.amazoncognito.com")
    monkeypatch.setattr(cognito, "_signing_key", lambda token, cfg: KEY.public_key())
    monkeypatch.setattr(cognito, "email_for", lambda token, sub: EMAILS.get(sub, "ana@uni.org"))
    cognito._email_cache.clear()
    EMAILS.clear()
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    SessionLocal.configure(bind=engine)
    session = SessionLocal()
    app.dependency_overrides[get_db] = lambda: session
    yield
    app.dependency_overrides.clear()
    session.close()


EMAILS: dict[str, str] = {}
SessionLocal = sessionmaker()


def token(key=KEY, **overrides):
    claims = {
        "sub": "user-1",
        "iss": ISSUER,
        "client_id": CLIENT,
        "token_use": "access",
        "exp": int(time.time()) + 600,
        "scope": "openid email profile",
    }
    claims.update(overrides)
    claims = {k: v for k, v in claims.items() if v is not None}
    return jwt.encode(claims, key, algorithm="RS256", headers={"kid": "k1"})


def bearer(**kw):
    return {"Authorization": f"Bearer {token(**kw)}"}


client = TestClient(app)


def test_valid_token_gives_interested_role():
    r = client.get("/api/me", headers=bearer())
    assert r.status_code == 200
    assert r.json() == {"email": "ana@uni.org", "role": "interested"}


def test_missing_token_is_a_visitor():
    assert client.get("/api/me").status_code == 401


@pytest.mark.parametrize(
    "kw",
    [
        {"exp": int(time.time()) - 10},  # expired
        {"iss": "https://evil.example/pool"},  # another issuer
        {"token_use": "id"},  # ID token instead of access token
        {"client_id": "someone-else"},  # another App Client
        {"sub": None},  # required claim missing
    ],
)
def test_invalid_tokens_are_rejected(kw):
    assert client.get("/api/me", headers=bearer(**kw)).status_code == 401


def test_token_signed_with_another_key_is_rejected():
    h = {"Authorization": f"Bearer {token(key=OTHER_KEY)}"}
    assert client.get("/api/me", headers=h).status_code == 401


def test_garbage_token_is_rejected():
    assert client.get("/api/me", headers={"Authorization": "Bearer not-a-jwt"}).status_code == 401


def test_organizer_group_gives_organizer_role():
    r = client.get("/api/me", headers=bearer(**{"cognito:groups": ["organizer"]}))
    assert r.json()["role"] == "organizer"


def test_participant_group_gives_participant_role():
    r = client.get("/api/me", headers=bearer(**{"cognito:groups": ["participant"]}))
    assert r.json()["role"] == "participant"


def test_approved_request_gives_participant_role():
    with SessionLocal() as db:
        db.add(models.ParticipationRequest(email="ana@uni.org", message="hi", status="approved"))
        db.commit()
    assert client.get("/api/me", headers=bearer()).json()["role"] == "participant"


def test_pending_request_stays_interested():
    with SessionLocal() as db:
        db.add(models.ParticipationRequest(email="ana@uni.org", message="hi", status="pending"))
        db.commit()
    assert client.get("/api/me", headers=bearer()).json()["role"] == "interested"


def test_dev_header_is_ignored_in_cognito_mode():
    r = client.get("/api/me", headers={"X-Dev-User": "a@b.org:organizer"})
    assert r.status_code == 401


def test_endpoints_enforce_roles_with_cognito_identity():
    h = bearer()
    assert client.get("/api/participation-requests", headers=h).status_code == 403
    h = bearer(**{"cognito:groups": ["organizer"]})
    assert client.get("/api/participation-requests", headers=h).status_code == 200


def test_auth_config_is_public_and_has_no_secrets():
    r = client.get("/api/auth-config")
    assert r.json() == {
        "mode": "cognito",
        "issuer": ISSUER,
        "clientId": CLIENT,
        "domain": "https://example.auth.us-east-1.amazoncognito.com",
    }


def test_auth_config_in_dev_mode(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "dev")
    assert client.get("/api/auth-config").json() == {"mode": "dev"}


def test_missing_configuration_rejects_everything(monkeypatch):
    monkeypatch.delenv("COGNITO_USER_POOL_ID")
    monkeypatch.setattr(cognito, "_ENV_FILE", cognito.Path("/nonexistent"))
    assert client.get("/api/me", headers=bearer()).status_code == 401
    assert client.get("/api/auth-config").status_code == 503
