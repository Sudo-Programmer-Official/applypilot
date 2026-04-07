from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from threading import Lock

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings

try:
    import firebase_admin
    from firebase_admin import auth as firebase_auth
    from firebase_admin import credentials as firebase_credentials
except ImportError:  # pragma: no cover - handled at runtime when dependency is missing
    firebase_admin = None
    firebase_auth = None
    firebase_credentials = None


@dataclass(frozen=True)
class FirebaseIdentity:
    uid: str
    email: str = ""
    display_name: str = ""
    photo_url: str = ""


_bearer_scheme = HTTPBearer(auto_error=False)
_firebase_init_lock = Lock()


def _firebase_is_configured() -> bool:
    return bool(settings.firebase_project_id)


@lru_cache(maxsize=1)
def _firebase_credential_payload() -> dict | str | None:
    if settings.firebase_service_account_json:
        return json.loads(settings.firebase_service_account_json)
    if settings.firebase_service_account_path:
        return str(Path(settings.firebase_service_account_path).expanduser())
    return None


def _ensure_firebase_app() -> None:
    if not _firebase_is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Firebase authentication is not configured on the API.",
        )
    if firebase_admin is None or firebase_auth is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Firebase Admin SDK is not installed on the API runtime.",
        )

    try:
        firebase_admin.get_app()
        return
    except ValueError:
        pass

    with _firebase_init_lock:
        try:
            firebase_admin.get_app()
            return
        except ValueError:
            pass
        credential_payload = _firebase_credential_payload()
        if isinstance(credential_payload, dict):
            credential = firebase_credentials.Certificate(credential_payload)
            firebase_admin.initialize_app(credential, {"projectId": settings.firebase_project_id})
            return
        if isinstance(credential_payload, str):
            credential = firebase_credentials.Certificate(credential_payload)
            firebase_admin.initialize_app(credential, {"projectId": settings.firebase_project_id})
            return

        firebase_admin.initialize_app(options={"projectId": settings.firebase_project_id})


def _verify_identity(token: str) -> FirebaseIdentity:
    _ensure_firebase_app()

    try:
        decoded_token = firebase_auth.verify_id_token(token)
    except Exception as exc:  # pragma: no cover - third-party exceptions depend on runtime
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firebase token verification failed.",
        ) from exc

    return FirebaseIdentity(
        uid=str(decoded_token.get("uid") or ""),
        email=str(decoded_token.get("email") or ""),
        display_name=str(decoded_token.get("name") or decoded_token.get("email") or ""),
        photo_url=str(decoded_token.get("picture") or ""),
    )


def optional_firebase_identity(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> FirebaseIdentity | None:
    if credentials is None:
        return None
    return _verify_identity(credentials.credentials)


def require_firebase_identity(
    identity: FirebaseIdentity | None = Depends(optional_firebase_identity),
) -> FirebaseIdentity:
    if identity is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sign in with Google to access private portfolio data.",
        )
    return identity
