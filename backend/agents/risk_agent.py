"""风控合规智能体 - 多维风控+合规校验+监管规则引擎"""
import logging
from typing import Any, Dict, List
from .base_agent import BaseAgent
from .tools import register_risk_tools
from .memory import get_agent_memory
from services.llm_service import llm_service
from config import MAX_SINGLE_STOCK_RATIO, MAX_SECTOR_RATIO, MAX_GEM_RATIO, COMPLIANCE_ENABLED

logger = logging.getLogger(__name__)


class RiskComplianceAgent(BaseAgent):
    """风控合规智能体：波动率风险+集中度风险+流动性风险+合规检查"""

    def __init__(self):
        super().__init__(
            name="风控合规智能体",
            agent_type="risk",
            description="评估投资风险，执行合规检查，确保投资建议符合监管要求。包括VaR计算、集中度检查、合规规则引擎",
            max_steps=6,
        )
        register_risk_tools(self)
        self.memory = get_agent_memory("risk")

    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        symbol = data.get("symbol", "")
        stock_data = data.get("stock_data", {})
        technical_data = data.get("technical_data", {})
        sentiment_data = data.get("sentiment_data", {})

        # 1. 波动率风险
        volatility_risk = self._calc_volatility_risk(stock_data, technical_data)

        # 2. 市场风险
        market_risk = self._calc_market_risk(stock_data)

        # 3. 舆情风险
        news_risk = self._calc_news_risk(sentiment_data)

        # 4. 流动性风险
        liquidity_risk = self._calc_liquidity_risk(stock_data)

        # 5. 综合风险评分
        overall_score = (volatility_risk * 0.35 + market_risk * 0.25 + news_risk * 0.25 + liquidity_risk * 0.15)
        risk_level = self._score_to_level(overall_score)

        # 6. 合规检查
        compliance_result = {}
        if COMPLIANCE_ENABLED:
            compliance_result = self._check_compliance(symbol, stock_data)

        # 7. 生成预警和缓解建议
        warnings = self._generate_warnings(volatility_risk, market_risk, news_risk, liquidity_risk, stock_data)
        mitigations = self._generate_mitigations(risk_level, warnings)

        analysis = self._generate_analysis(risk_level, overall_score, volatility_risk, market_risk, news_risk, liquidity_risk)
        key_findings = [f"综合风险等级: {risk_level}"]
        if volatility_risk > 0.7: key_findings.append(f"波动率风险偏高({volatility_risk:.2f})")
        if news_risk > 0.7: key_findings.append(f"舆情风险偏高({news_risk:.2f})")

        signal_map = {"low": "hold", "medium": "hold", "high": "sell", "critical": "strong_sell"}

        result = {
            "summary": analysis,
            "signal": signal_map.get(risk_level, "hold"),
            "confidence": round(min(0.5 + overall_score * 0.3, 0.9), 2),
            "analysis": analysis,
            "key_findings": key_findings,
            "risk_factors": warnings,
            "metadata": {
                "overall_risk": risk_level,
                "risk_score": round(overall_score, 3),
                "volatility_risk": round(volatility_risk, 3),
                "market_risk": round(market_risk, 3),
                "news_risk": round(news_risk, 3),
                "liquidity_risk": round(liquidity_risk, 3),
                "compliance": compliance_result,
                "risk_warnings": warnings,
                "risk_mitigations": mitigations,
            }
        }

        # LLM增强
        if llm_service.is_available():
            llm_result = await self._llm_analyze(
                system_prompt="你是专业金融风控专家，评估投资风险和合规性。用中文回答。",
                user_prompt=f"股票: {symbol}\n波动率风险: {volatility_risk:.3f}\n市场风险: {market_risk:.3f}\n舆情风险: {news_risk:.3f}\n流动性风险: {liquidity_risk:.3f}\n综合风险: {overall_score:.3f}({risk_level})\n合规: {compliance_result}",
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

        self.memory.record_episode("risk_assessment", f"评估{symbol}风险", result)
        return result

    def _calc_volatility_risk(self, stock_data, technical_data) -> float:
        risk = 0.5
        atr = technical_data.get("metadata", {}).get("atr_14") if isinstance(technical_data, dict) else None
        price = stock_data.get("current_price", 0)
        if atr and price and price > 0:
            vol_pct = (atr / price) * 100
            if vol_pct > 4: risk = 0.9
            elif vol_pct > 3: risk = 0.7
            elif vol_pct > 2: risk = 0.6
            elif vol_pct > 1: risk = 0.4
            else: risk = 0.3
        return risk

    def _calc_market_risk(self, stock_data) -> float:
        risk = 0.5
        beta = stock_data.get("beta")
        if beta:
            if beta > 2: risk = 0.9
            elif beta > 1.5: risk = 0.75
            elif beta > 1: risk = 0.6
            elif beta > 0.5: risk = 0.4
            else: risk = 0.3
        return risk

    def _calc_news_risk(self, sentiment_data) -> float:
        risk = 0.5
        if isinstance(sentiment_data, dict):
            score = sentiment_data.get("metadata", {}).get("sentiment_score", 0) if "metadata" in sentiment_data else 0
            if score < -0.5: risk = 0.85
            elif score < -0.3: risk = 0.7
            elif score < -0.1: risk = 0.6
            elif score > 0.3: risk = 0.35
        return risk

    def _calc_liquidity_risk(self, stock_data) -> float:
        risk = 0.3
        volume = stock_data.get("volume", 0)
        if volume < 100000: risk = 0.8
        elif volume < 500000: risk = 0.6
        elif volume < 1000000: risk = 0.5
        elif volume < 5000000: risk = 0.4
        return risk

    def _score_to_level(self, score: float) -> str:
        if score >= 0.75: return "critical"
        if score >= 0.6: return "high"
        if score >= 0.4: return "medium"
        return "low"

    def _check_compliance(self, symbol: str, stock_data: Dict) -> Dict:
        """合规检查引擎"""
        checks = {"passed": True, "violations": [], "warnings": []}
        # ST股检查
        name = stock_data.get("name", "")
        if "ST" in name or "*ST" in name:
            checks["passed"] = False
            checks["violations"].append(f"禁止买入ST股: {name}")
        # 创业板检查
        if symbol.startswith("300"):
            checks["warnings"].append(f"创业板股票({symbol})，需注意仓位限制(不超过{MAX_GEM_RATIO:.0%})")
        # 科创板检查
        if symbol.startswith("688"):
            checks["warnings"].append(f"科创板股票({symbol})，涨跌幅限制20%")
        return checks

    def _generate_warnings(self, vol, market, news, liquidity, stock_data) -> List[str]:
        warnings = []
        if vol > 0.7: warnings.append("⚠️ 高波动率: 价格波动剧烈")
        if market > 0.7: warnings.append("⚠️ 高市场敏感度: 随大盘波动较大")
        if news > 0.7: warnings.append("⚠️ 负面舆情: 近期新闻偏负面")
        if liquidity > 0.6: warnings.append("⚠️ 流动性风险: 成交量偏低")
        beta = stock_data.get("beta")
        if beta and beta > 1.5: warnings.append(f"⚠️ 高Beta({beta:.2f}): 放大市场波动")
        return warnings

    def _generate_mitigations(self, level, warnings) -> List[str]:
        mitigations = []
        if level in ["high", "critical"]:
            mitigations.append("建议设置止损单控制下行风险")
            mitigations.append("考虑降低仓位控制风险敞口")
        if any("波动" in w for w in warnings): mitigations.append("考虑期权对冲策略")
        if any("流动性" in w for w in warnings): mitigations.append("使用限价单避免滑点")
        if not mitigations: mitigations.append("标准风险管理措施适用")
        return mitigations

    def _generate_analysis(self, level, score, vol, market, news, liquidity) -> str:
        level_names = {"low": "低", "medium": "中等", "high": "高", "critical": "极高"}
        return f"综合风险等级: {level_names.get(level, level)}(评分{score:.2f}/1.0)。波动率风险{vol:.2f}，市场风险{market:.02f}，舆情风险{news:.2f}，流动性风险{liquidity:.2f}。"
