"""
数据库服务
支持SQLite(开发)和PostgreSQL(生产)
内存存储为主，数据库为可选持久化
"""
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class DatabaseService:
    """数据库服务 - 分析记录、审计日志、预警记录"""

    def __init__(self):
        self._initialized = False
        self._engine = None

    async def _ensure_init(self):
        """确保数据库已初始化"""
        if not self._initialized:
            await self._init_db()
            self._initialized = True

    async def _init_db(self):
        """初始化数据库（可选，失败不影响运行）"""
        try:
            from config import DATABASE_URL
            import sqlalchemy as sa
            # SQLite需要用同步引擎
            url = DATABASE_URL
            if url.startswith("sqlite:///") and "+aiosqlite" not in url:
                url = url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
            try:
                engine = sa.create_async_engine(url)
                async with engine.begin() as conn:
                    await conn.run_sync(self._create_tables_sync)
                self._engine = engine
                logger.info("数据库初始化完成")
            except Exception as e1:
                # 异步引擎失败，尝试同步
                sync_url = DATABASE_URL.replace("+aiosqlite", "")
                engine = sa.create_engine(sync_url)
                self._create_tables_sync(engine)
                self._engine = engine
                logger.info("数据库初始化完成(同步模式)")
        except Exception as e:
            logger.warning(f"数据库初始化失败: {e}，将使用内存存储")

    @staticmethod
    def _create_tables_sync(engine):
        """创建数据表"""
        import sqlalchemy as sa
        metadata = sa.MetaData()
        sa.Table("analyses", metadata,
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("symbol", sa.String(20)),
            sa.Column("company_name", sa.String(200)),
            sa.Column("current_price", sa.Float),
            sa.Column("recommendation", sa.Text),
            sa.Column("agent_results", sa.Text),
            sa.Column("processing_time", sa.Float),
            sa.Column("created_at", sa.DateTime, default=datetime.now),
        )
        sa.Table("audit_log", metadata,
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("timestamp", sa.DateTime),
            sa.Column("method", sa.String(10)),
            sa.Column("path", sa.String(500)),
            sa.Column("client_ip", sa.String(50)),
            sa.Column("status_code", sa.Integer),
            sa.Column("processing_time", sa.Float),
        )
        sa.Table("alerts", metadata,
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("alert_type", sa.String(50)),
            sa.Column("severity", sa.String(20)),
            sa.Column("title", sa.String(500)),
            sa.Column("message", sa.Text),
            sa.Column("symbol", sa.String(20)),
            sa.Column("timestamp", sa.DateTime, default=datetime.now),
        )
        sa.Table("reports", metadata,
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("report_type", sa.String(50)),
            sa.Column("title", sa.String(500)),
            sa.Column("content", sa.Text),
            sa.Column("summary", sa.Text),
            sa.Column("symbols", sa.Text),
            sa.Column("created_at", sa.DateTime, default=datetime.now),
        )
        metadata.create_all(engine)

    # 内存存储（数据库不可用时的降级方案）
    _memory_analyses: List[Dict] = []
    _memory_audit: List[Dict] = []
    _memory_alerts: List[Dict] = []
    _memory_reports: List[Dict] = []

    async def save_analysis(self, data: Dict):
        """保存分析记录"""
        self._memory_analyses.append({**data, "created_at": datetime.now().isoformat()})
        if len(self._memory_analyses) > 1000:
            self._memory_analyses = self._memory_analyses[-500:]

    async def save_audit_log(self, data: Dict):
        """保存审计日志"""
        self._memory_audit.append(data)
        if len(self._memory_audit) > 5000:
            self._memory_audit = self._memory_audit[-2000:]
        # 持久化到数据库
        try:
            await self._ensure_init()
            if self._engine is not None:
                import sqlalchemy as sa
                async with self._engine.begin() as conn:
                    await conn.execute(
                        sa.text(
                            "INSERT INTO audit_log (timestamp, method, path, client_ip, status_code, processing_time) "
                            "VALUES (:timestamp, :method, :path, :client_ip, :status_code, :processing_time)"
                        ),
                        data,
                    )
        except Exception as e:
            logger.warning(f"审计日志持久化失败: {e}")

    async def save_alert(self, alert: Dict):
        """保存预警记录"""
        self._memory_alerts.append({**alert, "timestamp": datetime.now().isoformat()})
        if len(self._memory_alerts) > 500:
            self._memory_alerts = self._memory_alerts[-200:]

    async def save_report(self, report: Dict):
        """保存报告记录"""
        self._memory_reports.append({**report, "created_at": datetime.now().isoformat()})
        if len(self._memory_reports) > 200:
            self._memory_reports = self._memory_reports[-100:]

    async def get_alerts(self, limit: int = 20) -> List[Dict]:
        """获取预警列表"""
        return self._memory_alerts[-limit:]

    async def get_reports(self, report_type: str = None, limit: int = 20) -> List[Dict]:
        """获取报告列表"""
        reports = self._memory_reports
        if report_type:
            reports = [r for r in reports if r.get("report_type") == report_type]
        return reports[-limit:]

    async def get_audit_log(self, limit: int = 50) -> List[Dict]:
        """获取审计日志"""
        return self._memory_audit[-limit:]


# 单例
db_service = DatabaseService()
