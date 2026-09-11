"""Аутентификация: пароль и WebAuthn."""

from __future__ import annotations

import logging
import secrets
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import (
    bytes_to_base64url,
    parse_authentication_credential_json,
    parse_registration_credential_json,
)
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from panel.config import settings
from panel.db import get_db
from panel.models import WebAuthnCredential

logger = logging.getLogger("panel.auth")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_serializer = URLSafeTimedSerializer(settings.panel_secret, salt="panel-session")
_pending_webauthn: dict[str, bytes] = {}


def verify_password(plain: str) -> bool:
    """Проверяет пароль панели."""
    stored = settings.panel_password
    if stored.startswith("$2"):
        return pwd_context.verify(plain, stored)
    return secrets.compare_digest(plain, stored)


def hash_password(plain: str) -> str:
    """Хеш пароля для .env."""
    return pwd_context.hash(plain)


def create_session_token() -> str:
    """Подписанный cookie-токен."""
    return _serializer.dumps({"auth": True})


def read_session_token(token: str) -> bool:
    """Валидирует cookie."""
    try:
        data = _serializer.loads(token, max_age=settings.session_max_age)
        return bool(data.get("auth"))
    except (BadSignature, SignatureExpired):
        return False


def require_auth(request: Request) -> None:
    """Dependency: требует сессию."""
    token = request.cookies.get(settings.session_cookie)
    if not token or not read_session_token(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized")


def is_authenticated(request: Request) -> bool:
    """Флаг авторизации для шаблонов."""
    token = request.cookies.get(settings.session_cookie)
    return bool(token and read_session_token(token))


def start_webauthn_registration() -> str:
    """Опции регистрации passkey (JSON)."""
    options = generate_registration_options(
        rp_id=settings.rp_id,
        rp_name=settings.rp_name,
        user_id=b"panel-admin",
        user_name="admin",
        user_display_name="Admin",
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
    )
    _pending_webauthn["reg"] = options.challenge
    return options_to_json(options)


def finish_webauthn_registration(credential: dict[str, Any], db: Session) -> None:
    """Сохраняет passkey после регистрации."""
    challenge = _pending_webauthn.pop("reg", None)
    if not challenge:
        raise HTTPException(status_code=400, detail="no registration challenge")
    parsed = parse_registration_credential_json(credential)
    verification = verify_registration_response(
        credential=parsed,
        expected_challenge=challenge,
        expected_rp_id=settings.rp_id,
        expected_origin=settings.origin,
    )
    db.add(
        WebAuthnCredential(
            credential_id=bytes_to_base64url(verification.credential_id),
            public_key=bytes_to_base64url(verification.credential_public_key),
            sign_count=verification.sign_count,
        )
    )
    db.commit()
    logger.info("webauthn credential registered")


def start_webauthn_authentication(db: Session) -> str:
    """Опции входа по passkey (JSON)."""
    rows = db.query(WebAuthnCredential).all()
    allow = [
        PublicKeyCredentialDescriptor(id=_b64url_to_bytes(r.credential_id)) for r in rows
    ]
    options = generate_authentication_options(
        rp_id=settings.rp_id,
        allow_credentials=allow,
        user_verification=UserVerificationRequirement.PREFERRED,
    )
    _pending_webauthn["auth"] = options.challenge
    return options_to_json(options)


def finish_webauthn_authentication(credential: dict[str, Any], db: Session) -> None:
    """Проверяет passkey-вход."""
    challenge = _pending_webauthn.pop("auth", None)
    if not challenge:
        raise HTTPException(status_code=400, detail="no authentication challenge")
    parsed = parse_authentication_credential_json(credential)
    cred_id = bytes_to_base64url(parsed.raw_id)
    row = db.query(WebAuthnCredential).filter(WebAuthnCredential.credential_id == cred_id).first()
    if row is None:
        raise HTTPException(status_code=400, detail="unknown credential")
    from webauthn.helpers import base64url_to_bytes

    verification = verify_authentication_response(
        credential=parsed,
        expected_challenge=challenge,
        expected_rp_id=settings.rp_id,
        expected_origin=settings.origin,
        credential_public_key=base64url_to_bytes(row.public_key),
        credential_current_sign_count=row.sign_count,
    )
    row.sign_count = verification.new_sign_count
    db.commit()


def _b64url_to_bytes(value: str) -> bytes:
    from webauthn.helpers import base64url_to_bytes

    return base64url_to_bytes(value)


AuthDep = Depends(require_auth)
DbDep = Depends(get_db)
