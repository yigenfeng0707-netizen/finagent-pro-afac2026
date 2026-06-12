"""风险计算服务"""
import logging
import numpy as np
from typing import Any, Dict

logger = logging.getLogger(__name__)


class RiskService:
    """风险计算服务"""

    async def calculate_var(self, symbol: str, confidence: float = 0.95, period: int = 1) -> Dict[str, Any]:
        """计算VaR(风险价值)"""
        from services.market_data import market_data_service
        df = await market_data_service.get_historical_data(symbol, period="1y")
        if df.empty:
            return {"var": 0, "method": "historical", "confidence": confidence}

        returns = df['Close'].pct_change().dropna()
        if len(returns) < 30:
            return {"var": 0, "method": "historical", "confidence": confidence}

        # 历史模拟法
        var_percentile = 1 - confidence
        var_daily = np.percentile(returns, var_percentile * 100)
        var_period = var_daily * np.sqrt(period)

        return {
            "var": round(var_period, 4),
            "var_daily": round(var_daily, 4),
            "method": "historical_simulation",
            "confidence": confidence,
            "period_days": period,
            "interpretation": f"在{confidence:.0%}置信度下，{period}日最大可能损失为{abs(var_period):.2%}"
        }


# 单例
risk_service = RiskService()
