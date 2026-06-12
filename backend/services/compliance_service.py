"""合规服务 - 监管规则引擎"""
import logging
from typing import Any, Dict
from config import MAX_SINGLE_STOCK_RATIO, MAX_SECTOR_RATIO, MAX_GEM_RATIO

logger = logging.getLogger(__name__)


class ComplianceService:
    """合规检查服务"""

    def __init__(self):
        self.rules = {
            "单股集中度": {"limit": MAX_SINGLE_STOCK_RATIO, "description": f"单一标的不超过组合{MAX_SINGLE_STOCK_RATIO:.0%}"},
            "行业集中度": {"limit": MAX_SECTOR_RATIO, "description": f"单一行业不超过组合{MAX_SECTOR_RATIO:.0%}"},
            "创业板限制": {"limit": MAX_GEM_RATIO, "description": f"创业板合计不超过{MAX_GEM_RATIO:.0%}"},
            "ST股禁止": {"limit": 0, "description": "禁止买入ST/*ST股"},
            "科创板注意": {"limit": None, "description": "科创板涨跌幅20%，需特别关注"},
        }

    async def check(self, symbol: str, action: str = "buy", portfolio: Dict = None) -> Dict[str, Any]:
        """执行合规检查"""
        result = {"passed": True, "violations": [], "warnings": []}

        # ST股检查
        if action == "buy":
            name = portfolio.get("name", "") if portfolio else ""
            if "ST" in symbol or "ST" in name:
                result["passed"] = False
                result["violations"].append(self.rules["ST股禁止"]["description"])

        # 创业板检查
        if symbol.startswith("300"):
            result["warnings"].append(self.rules["创业板限制"]["description"])

        # 科创板检查
        if symbol.startswith("688"):
            result["warnings"].append(self.rules["科创板注意"]["description"])

        # 集中度检查
        if portfolio and action == "buy":
            total = portfolio.get("total_value", 0)
            if total > 0:
                existing = portfolio.get("holdings", [])
                for h in existing:
                    ratio = h.get("value", 0) / total
                    if ratio > MAX_SINGLE_STOCK_RATIO:
                        result["warnings"].append(f"{h.get('symbol', '')}集中度{ratio:.0%}超过{MAX_SINGLE_STOCK_RATIO:.0%}限制")

        return result

    async def check_concentration(self, portfolio: Dict) -> Dict[str, Any]:
        """检查持仓集中度"""
        holdings = portfolio.get("holdings", [])
        total = sum(h.get("value", 0) for h in holdings)
        if total == 0:
            return {"status": "ok", "concentration_risks": []}

        risks = []
        for h in holdings:
            ratio = h.get("value", 0) / total
            if ratio > MAX_SINGLE_STOCK_RATIO:
                risks.append({"symbol": h.get("symbol", ""), "ratio": round(ratio, 3), "limit": MAX_SINGLE_STOCK_RATIO, "type": "单股集中度超标"})

        return {"status": "risk" if risks else "ok", "concentration_risks": risks}


# 单例
compliance_service = ComplianceService()
