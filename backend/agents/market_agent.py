"""市场分析智能体 - A股技术分析+基本面分析"""
import logging
from typing import Any, Dict, List
from .base_agent import BaseAgent
from .tools import register_market_tools
from .memory import get_agent_memory
from services.llm_service import llm_service

logger = logging.getLogger(__name__)


class MarketAnalysisAgent(BaseAgent):
    """市场分析智能体：技术指标+基本面+资金流向+行业对比"""

    def __init__(self):
        super().__init__(
            name="市场分析智能体",
            agent_type="market",
            description="专注于A股市场技术分析和基本面分析，计算RSI/MACD/KDJ等技术指标，分析PE/PB/ROE等估值指标，追踪资金流向和机构行为",
            max_steps=8,
        )
        register_market_tools(self)
        self.memory = get_agent_memory("market")

    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        symbol = data.get("symbol", "")
        stock_data = data.get("stock_data", {})

        # 1. 获取技术指标
        from services.market_data import market_data_service
        indicators = await market_data_service.calculate_technical_indicators(symbol)
        if "error" in indicators:
            indicators = {}

        # 2. 分析技术信号
        technical_signals = self._analyze_technical_signals(indicators)
        technical_signal = self._determine_signal(technical_signals)
        technical_confidence = self._calculate_confidence(indicators, technical_signals)

        # 3. 分析基本面
        fundamental_data = await market_data_service.get_financial_data(symbol)
        fundamental_analysis = self._analyze_fundamentals(fundamental_data or stock_data)

        # 4. 资金流向分析
        capital_flow = await market_data_service.get_capital_flow(symbol)

        # 5. 综合分析
        analysis_text = self._generate_analysis(indicators, technical_signals, fundamental_analysis, capital_flow, stock_data)

        # 6. 提取关键发现和风险
        key_findings = self._extract_findings(indicators, technical_signals, fundamental_analysis, capital_flow)
        risk_factors = self._extract_risks(indicators, fundamental_analysis)

        # 综合信号
        signals = [technical_signal]
        if fundamental_analysis.get("signal"):
            signals.append(fundamental_analysis["signal"])
        combined_signal = self._combine_signals(signals)

        result = {
            "summary": analysis_text,
            "signal": combined_signal,
            "confidence": round(technical_confidence, 2),
            "analysis": analysis_text,
            "key_findings": key_findings,
            "risk_factors": risk_factors,
            "metadata": {
                "indicators": indicators,
                "technical_signal": technical_signal,
                "fundamental_signal": fundamental_analysis.get("signal", "hold"),
                "atr_14": indicators.get("atr_14"),
            }
        }

        # LLM增强
        if llm_service.is_available():
            llm_result = await self._llm_analyze(
                system_prompt="你是专业A股分析师，基于技术指标和基本面数据给出分析判断。用中文回答。",
                user_prompt=f"股票: {symbol}\n技术指标: {indicators}\n技术信号: {technical_signals}\n基本面: {fundamental_analysis}\n资金流向: {capital_flow}",
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
                result["analysis"] = llm_result.get("analysis", result["analysis"])
                result["signal"] = llm_result.get("signal", result["signal"])
                result["confidence"] = llm_result.get("confidence", result["confidence"])
                result["key_findings"] = llm_result.get("key_findings", result["key_findings"])
                result["risk_factors"] = llm_result.get("risk_factors", result["risk_factors"])
                result["llm_enhanced"] = True

        # 记录到记忆
        self.memory.record_episode("stock_analysis", f"分析{symbol}", result)

        return result

    def _analyze_technical_signals(self, indicators: Dict) -> List[Dict]:
        """分析技术指标信号"""
        signals = []
        rsi = indicators.get("rsi_14")
        if rsi:
            if rsi > 70: signals.append({"indicator": "RSI", "signal": "overbought", "strength": "strong"})
            elif rsi < 30: signals.append({"indicator": "RSI", "signal": "oversold", "strength": "strong"})
            elif rsi > 60: signals.append({"indicator": "RSI", "signal": "bullish", "strength": "moderate"})
            elif rsi < 40: signals.append({"indicator": "RSI", "signal": "bearish", "strength": "moderate"})

        macd = indicators.get("macd")
        macd_signal = indicators.get("macd_signal")
        if macd is not None and macd_signal is not None:
            if macd > macd_signal: signals.append({"indicator": "MACD", "signal": "bullish", "strength": "moderate"})
            else: signals.append({"indicator": "MACD", "signal": "bearish", "strength": "moderate"})

        price = indicators.get("current_price")
        sma_20 = indicators.get("sma_20")
        if price and sma_20:
            if price > sma_20: signals.append({"indicator": "SMA20", "signal": "bullish", "strength": "moderate"})
            else: signals.append({"indicator": "SMA20", "signal": "bearish", "strength": "moderate"})

        return signals

    def _determine_signal(self, signals: List[Dict]) -> str:
        """从技术信号确定综合信号"""
        if not signals: return "hold"
        bullish = sum(1 for s in signals if s["signal"] in ["bullish", "oversold"])
        bearish = sum(1 for s in signals if s["signal"] in ["bearish", "overbought"])
        total = len(signals)
        if total == 0: return "hold"
        ratio = bullish / total
        if ratio > 0.7: return "strong_buy"
        if ratio > 0.55: return "buy"
        if ratio < 0.3: return "strong_sell"
        if ratio < 0.45: return "sell"
        return "hold"

    def _calculate_confidence(self, indicators: Dict, signals: List[Dict]) -> float:
        conf = 0.5
        available = sum(1 for v in indicators.values() if v is not None)
        conf += min(available * 0.03, 0.2)
        strong = sum(1 for s in signals if s.get("strength") == "strong")
        conf += min(strong * 0.05, 0.2)
        return min(conf, 0.9)

    def _analyze_fundamentals(self, data: Dict) -> Dict:
        """基本面分析"""
        pe = data.get("pe_ratio")
        assessment = "neutral"
        details = []
        if pe is not None:
            if pe < 0: assessment = "negative"; details.append(f"负PE({pe:.1f})，公司亏损")
            elif pe < 15: assessment = "positive"; details.append(f"低PE({pe:.1f})，可能被低估")
            elif pe > 40: assessment = "cautious"; details.append(f"高PE({pe:.1f})，估值偏高")
            else: details.append(f"PE({pe:.1f})处于合理区间")

        signal_map = {"positive": "buy", "negative": "sell", "cautious": "hold", "neutral": "hold"}
        return {"assessment": assessment, "details": details, "signal": signal_map.get(assessment, "hold")}

    def _generate_analysis(self, indicators, signals, fundamental, capital_flow, stock_data) -> str:
        price = stock_data.get("current_price", 0)
        analysis = f"技术分析: 当前价¥{price}，"
        bullish = [s for s in signals if s["signal"] in ["bullish", "oversold"]]
        bearish = [s for s in signals if s["signal"] in ["bearish", "overbought"]]
        if bullish: analysis += f"看多指标: {', '.join(s['indicator'] for s in bullish)}。"
        if bearish: analysis += f"看空指标: {', '.join(s['indicator'] for s in bearish)}。"
        if fundamental.get("details"): analysis += f" 基本面: {fundamental['details'][0]}。"
        return analysis

    def _extract_findings(self, indicators, signals, fundamental, capital_flow) -> List[str]:
        findings = []
        rsi = indicators.get("rsi_14")
        if rsi:
            if rsi > 70: findings.append(f"RSI={rsi:.1f}，超买区间")
            elif rsi < 30: findings.append(f"RSI={rsi:.1f}，超卖区间")
        for d in fundamental.get("details", [])[:2]: findings.append(d)
        return findings[:5]

    def _extract_risks(self, indicators, fundamental) -> List[str]:
        risks = []
        rsi = indicators.get("rsi_14")
        if rsi and rsi > 80: risks.append("RSI极度超买，回调风险高")
        atr = indicators.get("atr_14")
        price = indicators.get("current_price", 0)
        if atr and price and (atr/price)*100 > 3: risks.append("波动率过高")
        pe = fundamental.get("details", [])
        if any("亏损" in d for d in pe): risks.append("公司处于亏损状态")
        return risks[:3]

    def _combine_signals(self, signals: List[str]) -> str:
        signal_map = {"strong_buy": 1.0, "buy": 0.5, "hold": 0, "sell": -0.5, "strong_sell": -1.0}
        avg = sum(signal_map.get(s, 0) for s in signals) / len(signals) if signals else 0
        if avg > 0.5: return "strong_buy"
        if avg > 0.15: return "buy"
        if avg < -0.5: return "strong_sell"
        if avg < -0.15: return "sell"
        return "hold"
