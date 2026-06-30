"""
认证中间件 - 从Authorization header提取token，验证并注入user_id和role
"""
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# 不需要认证的路径前缀
PUBLIC_PATHS = [
    "/api/auth/login",
    "/api/auth/register",
    "/api/health",
    "/api/app-config",
    "/api/cases",
    "/api/benchmark",
    "/api/stats",
    "/api/market/overview",
    "/docs",
    "/openapi.json",
    "/redoc",
]


class AuthMiddleware(BaseHTTPMiddleware):
    """认证中间件"""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # WebSocket 和静态文件跳过认证
        if path.startswith("/api/ws") or path.startswith("/assets") or path.endswith((".js", ".css", ".ico", ".svg", ".html")):
            return await call_next(request)

        # 公开路径跳过认证
        for public_path in PUBLIC_PATHS:
            if path == public_path or path.startswith(public_path + "/"):
                return await call_next(request)

        # 提取token
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            request.state.user_id = None
            request.state.user_role = None
            return await call_next(request)

        token = auth_header[7:]

        from services.user_service import user_service
        payload = user_service.verify_token(token)

        if payload is None:
            return JSONResponse(
                status_code=401,
                content={"detail": "无效或过期的登录凭证，请重新登录"}
            )

        request.state.user_id = int(payload.get("sub", 0))
        request.state.user_role = payload.get("role", "user")
        return await call_next(request)
