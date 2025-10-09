"""
Observability Middleware - Request/Response tracking and metrics
"""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from services.observability_service import observability


class ObservabilityMiddleware:
    """Middleware for request tracking and performance monitoring"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        request_id = str(uuid.uuid4())
        start_time = time.time()

        # Add request ID to headers
        scope["headers"].append((b"x-request-id", request_id.encode()))

        # Log request start
        observability.log_business_event(
            "request_start",
            {
                "method": request.method,
                "path": request.url.path,
                "user_agent": request.headers.get("user-agent", ""),
                "client_ip": request.client.host if request.client else "unknown",
            },
            request_id,
        )

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # Calculate response time
                duration = (time.time() - start_time) * 1000
                status_code = message["status"]

                # Log response
                observability.log_business_event(
                    "request_complete",
                    {
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": status_code,
                        "duration_ms": duration,
                    },
                    request_id,
                )

                # Send metrics
                observability.put_metric("RequestCount", 1)
                observability.put_metric("ResponseTime", duration, "Milliseconds")

                if status_code >= 500:
                    observability.put_metric("ServerErrors", 1)
                elif status_code >= 400:
                    observability.put_metric("ClientErrors", 1)
                else:
                    observability.put_metric("SuccessfulRequests", 1)

                # Add request ID to response headers
                message["headers"].append((b"x-request-id", request_id.encode()))

            await send(message)

        await self.app(scope, receive, send_wrapper)
