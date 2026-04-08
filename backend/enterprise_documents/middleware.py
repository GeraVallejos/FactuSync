from __future__ import annotations

import uuid

from enterprise_documents.request_context import reset_request_id, set_request_id


class RequestIdMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.headers.get("X-Request-Id") or uuid.uuid4().hex
        request.request_id = request_id
        token = set_request_id(request_id)
        try:
            response = self.get_response(request)
        finally:
            reset_request_id(token)
        response["X-Request-Id"] = request_id
        return response
