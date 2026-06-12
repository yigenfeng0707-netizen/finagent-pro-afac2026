"""报告生成智能体 - 自动生成专业金融分析报告"""
import logging
import uuid
from typing import Any, Dict, List
from datetime import datetime
from .base_agent import BaseAgent
from .memory import get_agent_memory
from services.llm_service import llm_service
from services.database_service import db_service

logger = logging.getLogger(__name__)


class ReportAgent(BaseAgent):
    """报告生成智能体：晨报/研报/风控周报/组合月报/事件快报"""

    def __init__(self):
        super().__init__(
            name="报告生成智能体",
            agent_type="report",
            description="自动生成专业金融分析报告，包括晨报、个股研报、风控周报、组合月报和事件快报",
            max_steps=5,
        )
        self.memory = get_agent_memory("report")

    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        report_type = data.get("report_type", "morning_daily")
        symbol = data.get("symbol", "")
        analysis_data = data.get("analysis_data", {})

        report = await self.generate_report(report_type, symbol, analysis_data)
        return report

    async def generate_report(self, report_type: str, symbol: str = None, analysis_data: Dict = None) -> Dict:
        """生成报告"""
        report_id = str(uuid.uuid4())[:8]
        now = datetime.now()

        templates = {
            "morning_daily": {"title": f"金融晨报 {now.strftime('%Y-%m-%d')}", "sections": ["隔夜市场", "今日关注", "持仓变动", "风险提示"]},
            "stock_research": {"title": f"个股研报: {symbol or 'N/A'}", "sections": ["公司概况", "财务分析", "估值分析", "投资建议", "风险提示"]},
            "risk_weekly": {"title": f"风控周报 {now.strftime('%Y第%W周')}", "sections": ["风险指标", "预警事件", "合规检查", "下周关注"]},
            "portfolio_monthly": {"title": f"组合月报 {now.strftime('%Y年%m月')}", "sections": ["业绩回顾", "持仓分析", "调仓建议", "下月展望"]},
            "event_flash": {"title": f"事件快报", "sections": ["事件概述", "影响分析", "操作建议"]},
        }

        template = templates.get(report_type, templates["morning_daily"])

        # LLM生成报告内容
        content = ""
        summary = template["title"]
        if llm_service.is_available():
            try:
                result = await llm_service.generate_structured(
                    system_prompt=f"你是专业金融报告撰写师。生成{template['title']}。用中文，格式规范，数据详实。",
                    user_prompt=f"报告类型: {report_type}\n股票: {symbol}\n分析数据: {analysis_data}\n需包含章节: {template['sections']}",
                    output_schema={
                        "type": "object",
                        "properties": {
                            "content": {"type": "string"},
                            "summary": {"type": "string"},
                            "key_points": {"type": "array", "items": {"type": "string"}}
                        }
                    }
                )
                content = result.get("content", "")
                summary = result.get("summary", "")
            except:
                content = f"# {template['title']}\n\n" + "\n\n".join(f"## {s}\n\n（待填充）" for s in template["sections"])
                summary = template["title"]
        else:
            content = f"# {template['title']}\n\n" + "\n\n".join(f"## {s}\n\n（待填充）" for s in template["sections"])
            summary = template["title"]

        report = {
            "report_id": report_id,
            "report_type": report_type,
            "title": template["title"],
            "content": content,
            "summary": summary,
            "symbols": [symbol] if symbol else [],
            "generated_at": now.isoformat(),
            "signal": "hold",
            "confidence": 0.7,
            "analysis": summary,
            "key_findings": [],
            "risk_factors": [],
        }

        await db_service.save_report(report)
        self.memory.record_episode("report", f"生成{report_type}", report)
        return report
