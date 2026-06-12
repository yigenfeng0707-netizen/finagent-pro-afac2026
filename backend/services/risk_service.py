"""风险计算服务"""
import logging
import numpy as np
from typing import Any, Dict

logger = logging.getLogger(__name__)


class RiskService:
    """风险计算服务"""

    async def calculate_var(self, symbol: str, confidence: float = 0.95, period: int = 1) -> Dict[str, Any]:
        """计算VaR(风险价值)"""
        try:
            from services.market_data import market_data_service
            df = await market_data_service.get_historical_data(symbol, period="1y")
        except Exception as e:
            logger.warning(f"获取历史数据失败: {e}，使用参数法兜底")
            return self._parametric_var_fallback(confidence, period)

        if df is None or df.empty:
            logger.warning(f"股票{symbol}历史数据为空，使用参数法兜底")
            return self._parametric_var_fallback(confidence, period)

        # 确保 Close 列存在且为数值
        if 'Close' not in df.columns:
            logger.warning(f"历史数据缺少Close列，使用参数法兜底")
            return self._parametric_var_fallback(confidence, period)

        close = df['Close'].dropna()
        if len(close) < 30:
            logger.warning(f"历史数据不足30条({len(close)}条)，使用参数法兜底")
            return self._parametric_var_fallback(confidence, period)

        returns = close.pct_change().dropna()
        if len(returns) < 20:
            logger.warning(f"收益率数据不足，使用参数法兜底")
            return self._parametric_var_fallback(confidence, period)

        # 历史模拟法
        var_percentile = 1 - confidence
        var_daily = np.percentile(returns, var_percentile * 100)
        var_period = var_daily * np.sqrt(period)

        # 补充参数法作为交叉验证
        from scipy import stats
        mean_ret = returns.mean()
        std_ret = returns.std()
        z_score = stats.norm.ppf(var_percentile)
        parametric_var = mean_ret + z_score * std_ret
        parametric_var_period = parametric_var * np.sqrt(period)

        return {
            "var": round(var_period, 4),
            "var_daily": round(var_daily, 4),
            "method": "historical_simulation",
            "parametric_var": round(parametric_var_period, 4),
            "confidence": confidence,
            "period_days": period,
            "data_points": len(returns),
            "interpretation": f"在{confidence:.0%}置信度下，{period}日最大可能损失为{abs(var_period):.2%}"
        }

    def _parametric_var_fallback(self, confidence: float = 0.95, period: int = 1) -> Dict[str, Any]:
        """参数法VaR兜底 - 当历史数据不可用时使用典型A股波动率估算"""
        try:
            from scipy import stats
            var_percentile = 1 - confidence
            z_score = stats.norm.ppf(var_percentile)
        except ImportError:
            # scipy不可用时使用近似z值
            z_map = {0.90: -1.28, 0.95: -1.645, 0.99: -2.33}
            z_score = z_map.get(confidence, -1.645)

        # A股典型日波动率约2%
        typical_daily_vol = 0.02
        var_daily = z_score * typical_daily_vol
        var_period = var_daily * np.sqrt(period)

        return {
            "var": round(var_period, 4),
            "var_daily": round(var_daily, 4),
            "method": "parametric_fallback",
            "confidence": confidence,
            "period_days": period,
            "data_points": 0,
            "note": "历史数据不足，使用参数法估算（基于A股典型波动率2%）",
            "interpretation": f"在{confidence:.0%}置信度下，{period}日最大可能损失约{abs(var_period):.2%}（估算值）"
        }


# 单例
risk_service = RiskService()
