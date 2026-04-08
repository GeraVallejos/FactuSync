from __future__ import annotations

from datetime import UTC, datetime, timedelta
import uuid

import jwt
from django.conf import settings
from django.utils import timezone


class TokenType:
    ACCESS = "access"
    REFRESH = "refresh"


def build_token(user_id: int, token_type: str) -> str:
    lifetime = (
        settings.JWT_ACCESS_LIFETIME_SECONDS
        if token_type == TokenType.ACCESS
        else settings.JWT_REFRESH_LIFETIME_SECONDS
    )
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "type": token_type,
        "jti": uuid.uuid4().hex,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=lifetime)).timestamp()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def decode_token(raw_token: str, expected_type: str) -> dict:
    payload = jwt.decode(raw_token, settings.SECRET_KEY, algorithms=["HS256"])
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError("Invalid token type.")
    return payload


def is_token_revoked(payload: dict) -> bool:
    jti = payload.get("jti")
    if not jti:
        return False

    from enterprise_documents.models import RevokedToken

    return RevokedToken.objects.filter(jti=jti).exists()


def revoke_refresh_payload(payload: dict) -> None:
    jti = payload.get("jti")
    exp = payload.get("exp")
    subject = payload.get("sub")
    if not jti or not exp or not subject:
        return

    from enterprise_documents.models import RevokedToken

    RevokedToken.objects.get_or_create(
        jti=jti,
        defaults={
            "user_id": int(subject),
            "token_type": RevokedToken.TokenKind.REFRESH,
            "expires_at": datetime.fromtimestamp(int(exp), tz=UTC),
        },
    )


def purge_expired_revoked_tokens() -> int:
    from enterprise_documents.models import RevokedToken

    deleted, _ = RevokedToken.objects.filter(expires_at__lt=timezone.now()).delete()
    return int(deleted)
