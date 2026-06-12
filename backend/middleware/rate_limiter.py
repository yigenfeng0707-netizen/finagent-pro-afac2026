import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from collections import defaultdict

logger = logging.getLogger(__name__)


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """API请求速率限制中间件"""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
        self._cleanup_counter = 0

    async def dispatch(self, request: Request, call_next):
        # 跳过WebSocket和静态文件
        if request.url.path.startswith("/ws") or request.url.path.startswith("/assets"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # 清理过期记录
        self.requests[client_ip] = [
            t for t in self.requests[client_ip] if now - t < 60
        ]

        # 定期清理所有过期IP键，防止内存泄漏
        self._cleanup_counter += 1
        if self._cleanup_counter >= 100:
            self._cleanup_counter = 0
            stale_ips = [ip for ip, times in self.requests.items() if not times]
            for ip in stale_ips:
                del self.requests[ip]

        if len(self.requests[client_ip]) >= self.requests_per_minute:
            logger.warning(f"速率限制触发: {client_ip}")
            return JSONResponse(
                status_code=429,
                content={"detail": "请求过于频繁，请稍后再试"}
            )

        self.requests[client_ip].append(now)
        response = await call_next(request)
        return response
