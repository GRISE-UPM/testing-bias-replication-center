"""Amazon Cognito integration (decision D6).

The SPA signs the user in at the Cognito Hosted UI (authorization code + PKCE) and
sends the Access Token in ``Authorization: Bearer``. This module only *validates*
that token; it never sees passwords.

Validation (as described in the course notes on Cognito/JWT):
  * the signature, checked against the public keys published at ``<issuer>/.well-known/jwks.json``
    (keys are cached in memory and refreshed when a token carries an unknown ``kid``);
  * ``iss`` equals the issuer of our User Pool;
  * the token is not expired;
  * ``token_use`` is ``access`` (an ID Token is signed with the same keys, so the signature
    alone cannot tell them apart);
  * ``client_id`` is our App Client.

The Access Token carries no e-mail. It is read from the Hosted UI ``/oauth2/userInfo``
endpoint with the same token (scope ``email``) and cached for a few minutes.
"""
import os
import time
from dataclasses import dataclass
from pathlib import Path

import httpx
import jwt
from jwt import PyJWKClient

_ENV_FILE = Path(
    os.getenv(
        "COGNITO_ENV_FILE",
        Path(__file__).resolve().parents[2] / "aws-scripts" / "cognito.generated.env",
    )
)
_EMAIL_TTL_SECONDS = 300


class CognitoError(Exception):
    """The token is invalid or Cognito is not configured."""


@dataclass(frozen=True)
class Settings:
    region: str
    user_pool_id: str
    client_id: str
    domain: str  # https://<prefix>.auth.<region>.amazoncognito.com

    @property
    def issuer(self) -> str:
        return f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}"


def _read_env_file() -> dict[str, str]:
    values: dict[str, str] = {}
    if _ENV_FILE.is_file():
        for line in _ENV_FILE.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, _, value = line.partition("=")
                values[key.strip()] = value.strip()
    return values


def settings() -> Settings | None:
    """Configuration from the environment, falling back to the file written by cognito.sh."""
    file_values = _read_env_file()

    def get(name: str) -> str:
        return os.getenv(name) or file_values.get(name, "")

    s = Settings(
        region=get("COGNITO_REGION"),
        user_pool_id=get("COGNITO_USER_POOL_ID"),
        client_id=get("COGNITO_CLIENT_ID"),
        domain=get("COGNITO_DOMAIN").rstrip("/"),
    )
    return s if all((s.region, s.user_pool_id, s.client_id, s.domain)) else None


_jwk_clients: dict[str, PyJWKClient] = {}


def _signing_key(token: str, cfg: Settings):
    """Public key that signed ``token``. Isolated so tests can replace it."""
    url = f"{cfg.issuer}/.well-known/jwks.json"
    client = _jwk_clients.setdefault(url, PyJWKClient(url, cache_keys=True, lifespan=3600))
    return client.get_signing_key_from_jwt(token).key


def verify_access_token(token: str) -> dict:
    cfg = settings()
    if cfg is None:
        raise CognitoError("Cognito is not configured")
    try:
        claims = jwt.decode(
            token,
            _signing_key(token, cfg),
            algorithms=["RS256"],
            issuer=cfg.issuer,
            options={"require": ["exp", "iss", "sub"], "verify_aud": False},
        )
    except jwt.PyJWTError as exc:
        raise CognitoError(str(exc)) from exc
    if claims.get("token_use") != "access":
        raise CognitoError("Not an access token")
    if claims.get("client_id") != cfg.client_id:
        raise CognitoError("Token was issued for another client")
    return claims


_email_cache: dict[str, tuple[float, str]] = {}


def email_for(token: str, sub: str) -> str:
    """E-mail of the user, from Cognito's userInfo endpoint (cached per user)."""
    cached = _email_cache.get(sub)
    if cached and cached[0] > time.monotonic():
        return cached[1]
    cfg = settings()
    if cfg is None:
        raise CognitoError("Cognito is not configured")
    try:
        r = httpx.get(
            f"{cfg.domain}/oauth2/userInfo",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        r.raise_for_status()
        email = (r.json().get("email") or "").strip().lower()
    except (httpx.HTTPError, ValueError) as exc:
        raise CognitoError("Could not read the user's e-mail") from exc
    if not email:
        raise CognitoError("The token has no e-mail (scope 'email' missing)")
    _email_cache[sub] = (time.monotonic() + _EMAIL_TTL_SECONDS, email)
    return email
