import time
import uuid
from datetime import UTC, datetime

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.database import async_session_factory
from app.models.audit_log import AuditLog

logger = structlog.get_logger()


def _extract_user_info(request: Request) -> dict:
    from app.core.security import decode_token

    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        payload = decode_token(auth_header[7:])
        if payload:
            return {
                "user_id": payload.get("sub"),
                "tenant_id": payload.get("tenant_id"),
                "role": payload.get("role"),
            }
    return {}


class AuditLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = str(uuid.uuid4())[:8]
        start_time = time.monotonic()

        request.state.request_id = request_id

        response = await call_next(request)

        duration_ms = round((time.monotonic() - start_time) * 1000, 2)

        log_data = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query": str(request.query_params) if request.query_params else None,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "timestamp": datetime.now(UTC).isoformat(),
        }

        if request.url.path.startswith("/api/v1"):
            if response.status_code >= 500:
                logger.error("request_completed", **log_data)
            elif response.status_code >= 400:
                logger.warning("request_completed", **log_data)
            else:
                logger.info("request_completed", **log_data)

            if request.method in ("POST", "PUT", "PATCH", "DELETE"):
                try:
                    user_info = _extract_user_info(request)
                    async with async_session_factory() as db:
                        audit = AuditLog(
                            tenant_id=uuid.UUID(user_info["tenant_id"]) if user_info.get("tenant_id") else None,
                            user_id=uuid.UUID(user_info["user_id"]) if user_info.get("user_id") else None,
                            action=f"{request.method} {request.url.path}",
                            resource_type=request.url.path.split("/")[3] if len(request.url.path.split("/")) > 3 else None,
                            resource_id=request.url.path.split("/")[-1] if len(request.url.path.split("/")) > 4 else None,
                            detail={"query": str(request.query_params) if request.query_params else None, "duration_ms": duration_ms},
                            ip_address=request.client.host if request.client else None,
                            user_agent=request.headers.get("user-agent"),
                            status_code=response.status_code,
                        )
                        db.add(audit)
                        await db.commit()
                except Exception:
                    pass

        response.headers["X-Request-ID"] = request_id
        return response
