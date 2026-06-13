"""
认证中间件 - 从Authorization header提取token，验证并注入user_id
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
            # 没有token时允许访问（兼容无认证模式），但user_id为空
            request.state.user_id = None
            return await call_next(request)

        token = auth_header[7:]  # 去掉 "Bearer " 前缀

        from services.user_service import user_service
        user_id = user_service.verify_token(token)

        if user_id is None:
            return JSONResponse(
                status_code=401,
                content={"detail": "无效或过期的登录凭证，请重新登录"}
            )

        request.state.user_id = user_id
        return await call_next(request)
