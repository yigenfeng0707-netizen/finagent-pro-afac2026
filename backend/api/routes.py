import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import Dict, Any

from models.schemas import (
    AnalysisRequest, AnalysisResponse, ChatRequest, ChatResponse,
    PortfolioRequest, ScheduledTaskRequest, ScheduledTaskInfo,
    AlertInfo, ReportInfo
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ===== 健康检查 =====

@router.get("/health", summary="健康检查")
async def health_check():
    """服务健康检查接口"""
    return {"status": "ok", "app": "FinAgent Pro", "version": "1.0.0"}


# ===== 股票分析 =====

@router.post("/analyze")
async def analyze_stock(request: AnalysisRequest):
    """对指定股票进行多智能体综合分析"""
    from agents.orchestrator import orchestrator
    result = await orchestrator.analyze_stock(
        symbol=request.symbol,
        analysis_type=request.analysis_type,
        include_news=request.include_news,
        include_risk=request.include_risk,
        include_strategy=request.include_strategy
    )
    return result


@router.get("/market/overview", summary="市场概览")
async def get_market_overview():
    """获取A股市场概览"""
    from services.market_data import market_data_service
    return await market_data_service.get_market_overview()


@router.get("/stock/{symbol}", summary="获取股票数据")
async def get_stock_data(symbol: str):
    """获取单只股票的实时数据"""
    from services.market_data import market_data_service
    data = await market_data_service.get_stock_data(symbol)
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return data


@router.get("/stock/{symbol}/chart", summary="获取K线图数据")
async def get_chart_data(symbol: str, period: str = "6mo"):
    """获取股票K线图数据"""
    from services.market_data import market_data_service
    return await market_data_service.get_chart_data(symbol, period)


# ===== 对话交互 =====

@router.post("/chat", response_model=ChatResponse, summary="与数字员工对话")
async def chat(request: ChatRequest):
    """与金融数字员工进行对话交互"""
    from agents.orchestrator import orchestrator
    return await orchestrator.chat(
        message=request.message,
        conversation_id=request.conversation_id,
        context=request.context
    )


# ===== 组合管理 =====

@router.post("/portfolio/analyze", summary="组合分析")
async def analyze_portfolio(request: PortfolioRequest):
    """分析投资组合的风险和配置建议"""
    from agents.strategy_agent import StrategyAgent
    agent = StrategyAgent()
    return await agent.analyze_portfolio(request.holdings, request.risk_tolerance)


# ===== 预警系统 =====

@router.get("/alerts", summary="获取预警列表")
async def get_alerts(limit: int = 20):
    """获取最近的预警信息"""
    from services.database_service import db_service
    return await db_service.get_alerts(limit=limit)


# ===== 报告系统 =====

@router.get("/reports", summary="获取报告列表")
async def get_reports(report_type: str = None, limit: int = 20):
    """获取生成的报告列表"""
    from services.database_service import db_service
    return await db_service.get_reports(report_type=report_type, limit=limit)


@router.post("/reports/generate", response_model=ReportInfo, summary="生成报告")
async def generate_report(report_type: str, symbol: str = None):
    """生成指定类型的金融报告"""
    from agents.report_agent import ReportAgent
    agent = ReportAgent()
    return await agent.generate_report(report_type=report_type, symbol=symbol)


# ===== 定时任务 =====

@router.get("/tasks", response_model=list[ScheduledTaskInfo], summary="获取定时任务列表")
async def get_scheduled_tasks():
    """获取所有定时任务"""
    from services.scheduler_service import scheduler_service
    return scheduler_service.get_tasks()


@router.post("/tasks", response_model=ScheduledTaskInfo, summary="创建定时任务")
async def create_scheduled_task(request: ScheduledTaskRequest):
    """创建新的定时任务"""
    from services.scheduler_service import scheduler_service
    return scheduler_service.create_task(
        task_type=request.task_type,
        cron_expression=request.cron_expression,
        params=request.params,
        enabled=request.enabled
    )


@router.delete("/tasks/{task_id}", summary="删除定时任务")
async def delete_scheduled_task(task_id: str):
    """删除定时任务"""
    from services.scheduler_service import scheduler_service
    scheduler_service.delete_task(task_id)
    return {"status": "deleted"}


# ===== 智能体状态 =====

@router.get("/agents/status", summary="获取智能体状态")
async def get_agent_status():
    """获取所有智能体的运行状态"""
    from agents.orchestrator import orchestrator
    return orchestrator.get_agent_status()


# ===== WebSocket实时推送 =====

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket实时推送：智能体进度、预警通知等"""
    from services.ws_manager import ws_manager
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # 处理客户端消息
            await ws_manager.handle_message(websocket, data)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


# ===== 合规审计 =====

@router.get("/audit/log", summary="获取合规审计日志")
async def get_audit_log(limit: int = 50):
    """获取操作审计日志"""
    from services.database_service import db_service
    return await db_service.get_audit_log(limit=limit)
