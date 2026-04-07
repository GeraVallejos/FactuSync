from __future__ import annotations

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import authentication, exceptions

from enterprise_documents.auth_tokens import TokenType, decode_token


class JWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        raw_token = request.COOKIES.get(settings.JWT_ACCESS_COOKIE_NAME)
        if not raw_token:
            return None
        try:
            payload = decode_token(raw_token, TokenType.ACCESS)
        except jwt.InvalidTokenError as exc:
            raise exceptions.AuthenticationFailed("Invalid access token.") from exc

        user_model = get_user_model()
        user = user_model.objects.filter(id=payload["sub"], is_active=True).first()
        if user is None:
            raise exceptions.AuthenticationFailed("User not found.")
        return (user, None)
