from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
from django.conf import settings


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
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=lifetime)).timestamp()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def decode_token(raw_token: str, expected_type: str) -> dict:
    payload = jwt.decode(raw_token, settings.SECRET_KEY, algorithms=["HS256"])
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError("Invalid token type.")
    return payload
