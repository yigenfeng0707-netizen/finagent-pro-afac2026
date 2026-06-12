"""定时任务调度服务"""
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from config import SCHEDULER_ENABLED, MORNING_REPORT_TIME, EVENING_REPORT_TIME

logger = logging.getLogger(__name__)


class SchedulerService:
    """定时任务调度服务"""

    def __init__(self):
        self._tasks: Dict[str, Dict] = {}
        self._scheduler = None
        self._running = False

        if SCHEDULER_ENABLED:
            self._init_default_tasks()

    def _init_default_tasks(self):
        """初始化默认定时任务"""
        hour, minute = map(int, MORNING_REPORT_TIME.split(":"))
        self._tasks["morning_report"] = {
            "task_id": "morning_report",
            "task_type": "morning_report",
            "cron_expression": f"{minute} {hour} * * 1-5",  # 工作日
            "params": {},
            "enabled": True,
            "description": "每日晨报自动生成",
        }
        hour2, minute2 = map(int, EVENING_REPORT_TIME.split(":"))
        self._tasks["evening_report"] = {
            "task_id": "evening_report",
            "task_type": "evening_report",
            "cron_expression": f"{minute2} {hour2} * * 1-5",
            "params": {},
            "enabled": True,
            "description": "每日收盘总结",
        }
        self._tasks["risk_scan"] = {
            "task_id": "risk_scan",
            "task_type": "risk_scan",
            "cron_expression": "*/30 9-15 * * 1-5",  # 交易时间每30分钟
            "params": {},
            "enabled": True,
            "description": "交易时间风险扫描",
        }

    def start(self):
        """启动调度器"""
        if not SCHEDULER_ENABLED:
            logger.info("定时任务调度器未启用")
            return
        try:
            from apscheduler.schedulers.asyncio import AsyncIOScheduler
            self._scheduler = AsyncIOScheduler()
            for task_id, task in self._tasks.items():
                if task.get("enabled"):
                    self._scheduler.add_job(
                        self._execute_task,
                        "cron",
                        **self._parse_cron(task["cron_expression"]),
                        id=task_id,
                        args=[task_id],
                    )
            self._scheduler.start()
            self._running = True
            logger.info(f"定时任务调度器已启动，{len(self._tasks)}个任务")
        except Exception as e:
            logger.warning(f"调度器启动失败: {e}")

    def shutdown(self):
        """关闭调度器"""
        if self._scheduler:
            self._scheduler.shutdown()
            self._running = False

    def _parse_cron(self, cron_str: str) -> Dict:
        """解析cron表达式"""
        parts = cron_str.split()
        keys = ["minute", "hour", "day", "month", "day_of_week"]
        return {k: v for k, v in zip(keys, parts) if v != "*"}

    async def _execute_task(self, task_id: str):
        """执行定时任务"""
        task = self._tasks.get(task_id)
        if not task:
            return
        logger.info(f"执行定时任务: {task_id}")
        try:
            from agents.execution_agent import ExecutionAgent
            agent = ExecutionAgent()
            # 映射任务类型到ExecutionAgent支持的task_type
            task_type = task["task_type"]
            mapped_type = self._map_task_type(task_type)
            await agent.execute({"task_type": mapped_type, **task.get("params", {})})
            task["last_run"] = datetime.now().isoformat()
        except Exception as e:
            logger.error(f"定时任务执行失败 [{task_id}]: {e}")

    @staticmethod
    def _map_task_type(task_type: str) -> str:
        """将调度任务类型映射到ExecutionAgent.analyze()支持的task_type"""
        task_type_map = {
            "morning_report": "morning_scan",
            "evening_report": "morning_scan",  # 收盘总结也使用巡检逻辑
            "risk_scan": "risk_scan",
            "price_alert": "price_alert",
            "morning_scan": "morning_scan",
        }
        return task_type_map.get(task_type, task_type)

    def get_tasks(self) -> List[Dict]:
        return list(self._tasks.values())

    def create_task(self, task_type: str, cron_expression: str, params: Dict = None, enabled: bool = True) -> Dict:
        import uuid
        task_id = str(uuid.uuid4())[:8]
        task = {"task_id": task_id, "task_type": task_type, "cron_expression": cron_expression, "params": params, "enabled": enabled}
        self._tasks[task_id] = task
        return task

    def delete_task(self, task_id: str):
        if task_id in self._tasks:
            del self._tasks[task_id]


# 单例
scheduler_service = SchedulerService() if SCHEDULER_ENABLED else None
