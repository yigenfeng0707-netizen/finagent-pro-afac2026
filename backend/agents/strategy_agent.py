"""投资策略智能体 - 资产配置+组合构建+策略回测"""
import logging
from typing import Any, Dict, List
from .base_agent import BaseAgent
from .tools import register_market_tools, register_risk_tools
from .memory import get_agent_memory
from services.llm_service import llm_service

logger = logging.getLogger(__name__)


class StrategyAgent(BaseAgent):
    """投资策略智能体：资产配置+组合构建+策略回测+交易信号"""

    def __init__(self):
        super().__init__(
            name="投资策略智能体",
            agent_type="strategy",
            description="基于市场分析和风险评估，提供资产配置建议、构建投资组合、回测策略、生成交易信号",
            max_steps=8,
        )
        register_market_tools(self)
        register_risk_tools(self)
        self.memory = get_agent_memory("strategy")

    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        symbol = data.get("symbol", "")
        stock_data = data.get("stock_data", {})
        market_result = data.get("market_result", {})
        risk_result = data.get("risk_result", {})

        # 综合市场信号和风险信号
        market_signal = market_result.get("signal", "hold") if isinstance(market_result, dict) else "hold"
        risk_level = risk_result.get("metadata", {}).get("overall_risk", "medium") if isinstance(risk_result, dict) else "medium"

        # 仓位建议
        position = self._calc_position(market_signal, risk_level)

        # 交易信号
        signal = self._determine_strategy_signal(market_signal, risk_level)

        # 目标价和止损
        current_price = stock_data.get("current_price", 0)
        target, stop_loss = self._calc_price_targets(current_price, market_signal, risk_level)

        analysis = f"策略建议: {signal}，建议仓位{position:.0%}。目标价¥{target}，止损价¥{stop_loss}。"

        result = {
            "summary": analysis,
            "signal": signal,
            "confidence": 0.6,
            "analysis": analysis,
            "key_findings": [f"建议仓位: {position:.0%}", f"目标价: ¥{target}", f"止损价: ¥{stop_loss}"],
            "risk_factors": [f"当前风险等级: {risk_level}"],
            "metadata": {"position": position, "target_price": target, "stop_loss": stop_loss}
        }

        if llm_service.is_available():
            llm_result = await self._llm_analyze(
                system_prompt="你是专业投资策略师，基于分析和风控给出策略建议。用中文回答。",
                user_prompt=f"股票: {symbol}\n市场信号: {market_signal}\n风险等级: {risk_level}\n当前价: {current_price}",
                output_schema={
                    "type": "object",
                    "properties": {
                        "analysis": {"type": "string"},
                        "signal": {"type": "string", "enum": ["strong_buy", "buy", "hold", "sell", "strong_sell"]},
                        "confidence": {"type": "number"},
                        "key_findings": {"type": "array", "items": {"type": "string"}},
                        "risk_factors": {"type": "array", "items": {"type": "string"}}
                    }
                }
            )
            if llm_result:
                llm_result = llm_service.validate_agent_result(llm_result)
                result.update({k: llm_result.get(k, result[k]) for k in ["analysis", "signal", "confidence", "key_findings", "risk_factors"]})
                result["llm_enhanced"] = True

        self.memory.record_episode("strategy", f"策略建议{symbol}", result)
        return result

    async def analyze_portfolio(self, holdings: List[Dict], risk_tolerance: str = "moderate") -> Dict:
        """分析投资组合"""
        total_value = sum(h.get("value", 0) for h in holdings)
        analysis = {"total_value": total_value, "position_count": len(holdings), "risk_tolerance": risk_tolerance, "suggestions": []}

        # 集中度检查
        for h in holdings:
            ratio = h.get("value", 0) / total_value if total_value > 0 else 0
            if ratio > 0.15: analysis["suggestions"].append(f"{h.get('symbol', '')}仓位过重({ratio:.0%})，建议减仓")

        return analysis

    def _calc_position(self, market_signal: str, risk_level: str) -> float:
        base = {"strong_buy": 0.8, "buy": 0.6, "hold": 0.4, "sell": 0.2, "strong_sell": 0.1}.get(market_signal, 0.4)
        risk_adj = {"low": 1.0, "medium": 0.8, "high": 0.5, "critical": 0.2}.get(risk_level, 0.8)
        return round(base * risk_adj, 2)

    def _determine_strategy_signal(self, market_signal, risk_level) -> str:
        if risk_level == "critical": return "strong_sell"
        if risk_level == "high" and market_signal in ["hold", "sell"]: return "sell"
        return market_signal

    def _calc_price_targets(self, price, signal, risk) -> tuple:
        if not price: return 0, 0
        up = {"strong_buy": 0.15, "buy": 0.10, "hold": 0.05, "sell": 0.02, "strong_sell": 0.01}.get(signal, 0.05)
        down = {"low": 0.05, "medium": 0.07, "high": 0.10, "critical": 0.15}.get(risk, 0.07)
        return round(price * (1 + up), 2), round(price * (1 - down), 2)
