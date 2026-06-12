import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import APP_NAME, APP_VERSION, DEBUG
from api.routes import router
from middleware.rate_limiter import RateLimiterMiddleware
from middleware.compliance_audit import ComplianceAuditMiddleware

logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""
    logger.info(f"🚀 {APP_NAME} v{APP_VERSION} 启动中...")
    # 启动时初始化调度器
    from services.scheduler_service import scheduler_service
    if scheduler_service:
        scheduler_service.start()
        logger.info("📅 定时任务调度器已启动")
    yield
    # 关闭时清理
    if scheduler_service:
        scheduler_service.shutdown()
        logger.info("📅 定时任务调度器已关闭")
    logger.info(f"👋 {APP_NAME} 已关闭")


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="金融自主智能体平台 - 基于大语言模型与多智能体协同技术",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 自定义中间件
app.add_middleware(RateLimiterMiddleware)
app.add_middleware(ComplianceAuditMiddleware)

# 路由
app.include_router(router, prefix="/api")

# 静态文件
try:
    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")
except Exception:
    pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=DEBUG)
