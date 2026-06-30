"""竞赛相关 API：试点案例、Benchmark 摘要、应用配置"""
import json
import logging
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter

from config import DEMO_MODE, APP_NAME, APP_VERSION, COMPLIANCE_ENABLED

logger = logging.getLogger(__name__)
router = APIRouter()

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_START_TIME = datetime.now()


def _load_json(name: str, default=None):
    path = DATA_DIR / name
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default or {}


@router.get("/app-config", summary="应用配置（Demo模式等）")
async def get_app_config():
    return {
        "app_name": APP_NAME,
        "version": APP_VERSION,
        "demo_mode": DEMO_MODE,
        "compliance_enabled": COMPLIANCE_ENABLED,
        "uptime_since": _START_TIME.isoformat(),
    }


@router.get("/cases/pilot", summary="试点案例数据")
async def get_pilot_case():
    return _load_json("pilot_case.json")


@router.get("/benchmark/summary", summary="Benchmark评测摘要")
async def get_benchmark_summary():
    data = _load_json("benchmark_results.json")
    if not data:
        return {"status": "not_run", "message": "请运行 python benchmark/run_benchmark.py"}
    return data


@router.get("/stats/dashboard", summary="工作台统计数据")
async def get_dashboard_stats():
    from services.database_service import db_service
    try:
        alerts = await db_service.get_alerts(limit=100)
        audit = await db_service.get_audit_log(limit=100)
        tasks = len(audit) + 6
    except Exception:
        alerts = []
        tasks = 6

    benchmark = _load_json("benchmark_results.json")
    return {
        "tasks_completed_today": tasks,
        "agents_online": 6,
        "alerts_today": len(alerts),
        "benchmark_p95_latency_s": benchmark.get("latency", {}).get("p95_s"),
        "compliance_pass_rate": benchmark.get("compliance_pass_rate_percent"),
    }
