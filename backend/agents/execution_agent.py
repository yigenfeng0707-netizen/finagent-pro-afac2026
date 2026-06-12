"""执行监控智能体 - 定时巡检+实时监控+主动预警+自主任务"""
import logging
import uuid
from typing import Any, Dict, List
from datetime import datetime
from .base_agent import BaseAgent
from .memory import get_agent_memory
from services.llm_service import llm_service
from services.database_service import db_service
from services.ws_manager import ws_manager

logger = logging.getLogger(__name__)


class ExecutionAgent(BaseAgent):
    """执行监控智能体：定时巡检+实时监控+主动预警+自主任务执行"""

    def __init__(self):
        super().__init__(
            name="执行监控智能体",
            agent_type="execution",
            description="负责定时巡检、实时监控、主动预警和自主任务执行，推动金融服务从被动响应迈向主动智能",
            max_steps=5,
        )
        self.memory = get_agent_memory("execution")

    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        task_type = data.get("task_type", "scan")
        symbol = data.get("symbol", "")

        if task_type == "morning_scan":
            return await self._morning_scan()
        elif task_type == "risk_scan":
            return await self._risk_scan(data.get("portfolio", {}))
        elif task_type == "price_alert":
            return await self._price_alert(symbol, data.get("threshold", 0.05))
        else:
            return {"summary": "未知任务类型", "signal": "hold", "confidence": 0.3, "analysis": "", "key_findings": [], "risk_factors": []}

    async def _morning_scan(self) -> Dict[str, Any]:
        """晨间巡检"""
        from services.market_data import market_data_service
        overview = await market_data_service.get_market_overview()
        findings = []
        if overview.get("indices"):
            for idx in overview["indices"][:4]:
                change = idx.get("change_percent", 0)
                findings.append(f"{idx.get('name', '')}: {change:+.2f}%")

        result = {
            "summary": f"晨间巡检完成，扫描{len(overview.get('indices', []))}个指数",
            "signal": "hold",
            "confidence": 0.7,
            "analysis": "晨间巡检: " + "; ".join(findings),
            "key_findings": findings,
            "risk_factors": [],
        }
        self.memory.record_episode("morning_scan", "晨间巡检", result)
        return result

    async def _risk_scan(self, portfolio: Dict) -> Dict[str, Any]:
        """风险扫描"""
        alerts = []
        holdings = portfolio.get("holdings", [])
        for h in holdings:
            symbol = h.get("symbol", "")
            from services.market_data import market_data_service
            stock = await market_data_service.get_stock_data(symbol)
            change = stock.get("change_percent", 0)
            if change < -5:
                alert = {"alert_id": str(uuid.uuid4())[:8], "alert_type": "price", "severity": "high", "title": f"{symbol}大跌{change:.2f}%", "symbol": symbol}
                alerts.append(alert)
                await db_service.save_alert(alert)
                await ws_manager.send_alert(alert)

        return {
            "summary": f"风险扫描完成，发现{len(alerts)}个预警",
            "signal": "sell" if alerts else "hold",
            "confidence": 0.8,
            "analysis": f"扫描{len(holdings)}只持仓，{len(alerts)}个预警" + ("。" if not alerts else ": " + "; ".join(a["title"] for a in alerts)),
            "key_findings": [a["title"] for a in alerts],
            "risk_factors": [],
        }

    async def _price_alert(self, symbol: str, threshold: float = 0.05) -> Dict[str, Any]:
        """价格预警"""
        from services.market_data import market_data_service
        stock = await market_data_service.get_stock_data(symbol)
        change = abs(stock.get("change_percent", 0))
        triggered = change >= threshold * 100

        if triggered:
            alert = {"alert_id": str(uuid.uuid4())[:8], "alert_type": "price", "severity": "high", "title": f"{symbol}价格波动{change:.2f}%", "symbol": symbol}
            await db_service.save_alert(alert)
            await ws_manager.send_alert(alert)

        return {
            "summary": f"价格预警: {symbol} {'触发' if triggered else '未触发'}",
            "signal": "sell" if triggered else "hold",
            "confidence": 0.7,
            "analysis": f"{symbol}当前涨跌幅{stock.get('change_percent', 0):.2f}%，阈值{threshold*100:.0f}%",
            "key_findings": [f"涨跌幅: {stock.get('change_percent', 0):.2f}%"] if triggered else [],
            "risk_factors": [],
        }
