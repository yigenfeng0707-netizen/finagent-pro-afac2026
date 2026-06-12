import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from datetime import datetime

logger = logging.getLogger(__name__)


class ComplianceAuditMiddleware(BaseHTTPMiddleware):
    """合规审计中间件 - 记录所有涉及投资建议的API调用"""

    # 需要审计的路径
    AUDITED_PATHS = ["/api/analyze", "/api/chat", "/api/portfolio"]

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)

        # 审计投资建议相关请求
        if any(request.url.path.startswith(path) for path in self.AUDITED_PATHS):
            audit_record = {
                "timestamp": datetime.now().isoformat(),
                "method": request.method,
                "path": str(request.url.path),
                "client_ip": request.client.host if request.client else "unknown",
                "status_code": response.status_code,
                "processing_time": round(time.time() - start_time, 3)
            }
            logger.info(f"📋 合规审计: {audit_record}")

            # 异步写入审计日志
            try:
                from services.database_service import db_service
                await db_service.save_audit_log(audit_record)
            except Exception as e:
                logger.warning(f"审计日志写入失败: {e}")

        return response
