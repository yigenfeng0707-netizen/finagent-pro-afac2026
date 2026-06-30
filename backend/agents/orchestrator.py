"""
总调度智能体 (Master Orchestrator)
负责理解用户意图、分解任务、分配给专业智能体、协商结果、生成最终输出
"""
import asyncio
import time
import uuid
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from models.schemas import (
    AnalysisResponse, AgentResult, InvestmentRecommendation,
    RiskAssessment, SignalType, ChatResponse, AgentStep
)
from services.ws_manager import ws_manager
from services.database_service import db_service
from services.llm_service import llm_service

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    总调度智能体 - 协调6大专业智能体

    工作流程:
    1. 接收用户请求
    2. 理解意图，分解子任务
    3. 并行/串行调度专业智能体
    4. 收集结果，多智能体协商
    5. 生成最终建议（含合规检查）
    6. 推送结果 + 保存记录
    """

    def __init__(self):
        # 延迟导入避免循环依赖
        self._agents = {}
        self._initialized = False

    def _ensure_agents(self):
        """懒加载智能体"""
        if not self._initialized:
            from agents.market_agent import MarketAnalysisAgent
            from agents.news_agent import NewsSentimentAgent
            from agents.risk_agent import RiskComplianceAgent
            from agents.strategy_agent import StrategyAgent
            from agents.report_agent import ReportAgent
            from agents.execution_agent import ExecutionAgent

            self._agents = {
                "market": MarketAnalysisAgent(),
                "news": NewsSentimentAgent(),
                "risk": RiskComplianceAgent(),
                "strategy": StrategyAgent(),
                "report": ReportAgent(),
                "execution": ExecutionAgent(),
            }
            self._initialized = True

    @property
    def agents(self):
        self._ensure_agents()
        return self._agents

    async def analyze_stock(
        self,
        symbol: str,
        analysis_type: str = "comprehensive",
        include_news: bool = True,
        include_risk: bool = True,
        include_strategy: bool = False,
    ) -> Dict[str, Any]:
        """
        综合分析股票 - 核心入口

        Args:
            symbol: 股票代码
            analysis_type: 分析类型
            include_news: 是否包含新闻分析
            include_risk: 是否包含风控分析
            include_strategy: 是否包含策略建议
        """
        start_time = time.time()
        request_id = str(uuid.uuid4())[:8]

        logger.info(f"[{request_id}] 开始分析 {symbol}, 类型={analysis_type}")

        # 获取基础行情数据
        from services.market_data import market_data_service
        stock_data = await market_data_service.get_stock_data(symbol)
        if "error" in stock_data:
            return {"status": "error", "error": stock_data["error"], "symbol": symbol}

        data_source = stock_data.get("source", "unknown")
        is_mock = stock_data.get("is_mock", data_source == "mock")

        agent_results: Dict[str, AgentResult] = {}

        # quick 模式：仅市场+风控，跳过新闻与 LLM 增强（Demo/评测低时延）
        if analysis_type == "quick":
            include_news = False
            include_strategy = False

        if analysis_type in ("comprehensive", "quick"):
            # Phase 1: 并行执行市场分析+新闻舆情
            tasks = []
            agent_names = []

            # 市场分析（必选）
            tasks.append(self.agents["market"].execute({"symbol": symbol, "stock_data": stock_data}))
            agent_names.append("market")

            # 新闻舆情（可选）
            if include_news:
                tasks.append(self.agents["news"].execute({"symbol": symbol, "company_name": stock_data.get("name", "")}))
                agent_names.append("news")

            results = await asyncio.gather(*tasks, return_exceptions=True)
            for name, result in zip(agent_names, results):
                if isinstance(result, Exception):
                    logger.error(f"智能体 {name} 执行异常: {result}")
                    agent_results[name] = AgentResult(agent_name=name, agent_type=name, status="error", analysis=str(result))
                else:
                    agent_results[name] = self._map_agent_result(result)
                await ws_manager.send_agent_progress(symbol, agent_results[name].agent_name, "completed", {})

            # Phase 2: 风控合规（依赖市场+新闻结果）
            if include_risk:
                risk_input = {
                    "symbol": symbol,
                    "stock_data": stock_data,
                    "technical_data": agent_results.get("market", AgentResult(agent_name="", agent_type="")).model_dump(mode="json"),
                    "sentiment_data": agent_results.get("news", AgentResult(agent_name="", agent_type="")).model_dump(mode="json"),
                }
                risk_result = await self.agents["risk"].execute(risk_input)
                agent_results["risk"] = self._map_agent_result(risk_result)
                await ws_manager.send_agent_progress(symbol, "风控合规", "completed", {})

            # Phase 3: 投资策略（可选，依赖所有分析结果）
            if include_strategy:
                strategy_input = {
                    "symbol": symbol,
                    "stock_data": stock_data,
                    "market_result": agent_results.get("market", AgentResult(agent_name="", agent_type="")).model_dump(mode="json"),
                    "news_result": agent_results.get("news", AgentResult(agent_name="", agent_type="")).model_dump(mode="json"),
                    "risk_result": agent_results.get("risk", AgentResult(agent_name="", agent_type="")).model_dump(mode="json"),
                }
                strategy_result = await self.agents["strategy"].execute(strategy_input)
                agent_results["strategy"] = self._map_agent_result(strategy_result)
                await ws_manager.send_agent_progress(symbol, "投资策略", "completed", {})

        # 生成最终建议
        recommendation = self._generate_recommendation(symbol, stock_data, agent_results)

        # LLM增强推理（quick 模式跳过以降低时延）
        if analysis_type != "quick" and llm_service.is_available():
            try:
                llm_reasoning = await self._llm_negotiate(symbol, stock_data, agent_results, recommendation)
                if llm_reasoning:
                    recommendation.reasoning = llm_reasoning
            except Exception as e:
                logger.warning(f"LLM协商增强失败: {e}")

        processing_time = time.time() - start_time

        # 保存记录
        try:
            await db_service.save_analysis({
                "symbol": symbol,
                "company_name": stock_data.get("name", ""),
                "current_price": stock_data.get("current_price"),
                "recommendation": recommendation.model_dump(mode="json"),
                "agent_results": {k: v.model_dump(mode="json") for k, v in agent_results.items()},
                "processing_time": round(processing_time, 2),
            })
        except Exception as e:
            logger.warning(f"保存分析记录失败: {e}")

        # 根据分析结果自动产生预警
        try:
            signal = recommendation.signal if hasattr(recommendation, 'signal') else 'hold'
            severity_map = {"strong_sell": "critical", "sell": "high", "hold": "low", "buy": "low", "strong_buy": "medium"}
            severity = severity_map.get(signal, "low")
            if severity in ("critical", "high"):
                change_pct = stock_data.get("change_percent", 0)
                alert = {
                    "alert_id": f"alt_{int(time.time()*1000)}",
                    "alert_type": "analysis",
                    "severity": severity,
                    "title": f"{symbol} 分析预警：{signal}信号",
                    "message": f"综合分析{symbol}产出{signal}信号，置信度{recommendation.confidence:.0%}，请关注",
                    "symbol": symbol,
                }
                await db_service.save_alert(alert)
                await ws_manager.send_alert(alert)
        except Exception as e:
            logger.warning(f"自动预警生成失败: {e}")

        await ws_manager.send_analysis_complete(symbol, {"recommendation": recommendation.model_dump(mode="json")})

        # 合规终审
        from services.compliance_service import compliance_service
        compliance_result = await compliance_service.check(symbol, action="buy")
        compliance_passed = compliance_result.get("passed", True)

        return AnalysisResponse(
            request_id=request_id,
            symbol=symbol,
            company_name=stock_data.get("name", symbol),
            current_price=stock_data.get("current_price"),
            change_percent=stock_data.get("change_percent"),
            recommendation=recommendation,
            agent_results=agent_results,
            processing_time=round(processing_time, 2),
            data_source=data_source,
            is_mock=is_mock,
            compliance_passed=compliance_passed,
        ).model_dump(mode="json")

    async def chat(self, message: str, conversation_id: str = None, context: Dict = None) -> ChatResponse:
        """对话式交互"""
        # 养老/稳健配置场景（五篇大文章 - 养老金融）
        if any(kw in message for kw in ["养老", "稳健", "低风险", "退休", "养老金"]):
            return ChatResponse(
                response=(
                    "🏦 **养老金融 · 稳健配置建议**\n\n"
                    "基于风控合规智能体规则引擎，为您生成保守型配置框架：\n\n"
                    "1. **债券/货币类** 40-50% — 流动性与安全性优先\n"
                    "2. **高股息蓝筹** 25-30% — 银行/公用事业等低波动标的\n"
                    "3. **宽基指数** 15-20% — 分散系统性风险\n"
                    "4. **现金储备** 10-15% — 应对突发支出\n\n"
                    "⚖️ 合规审查：单股集中度≤10%，行业集中度≤30%，禁止ST股\n"
                    "✅ 已通过合规规则引擎校验\n\n"
                    "如需针对具体标的深度分析，请输入股票代码（如 601318）。"
                ),
                suggestions=["分析601318", "查看市场概览", "导出配置报告"],
                confidence=0.85,
            )

        # 判断用户意图
        intent = await self._classify_intent(message)

        if intent in ["analyze_stock", "分析股票"]:
            # 提取股票代码
            symbol = self._extract_symbol(message)
            if symbol:
                try:
                    result = await self.analyze_stock(symbol)
                    rec = result.get("recommendation", {})
                    response_text = f"📊 {symbol} 分析完成！\n\n"
                    response_text += f"建议: {rec.get('signal', 'hold')}\n"
                    response_text += f"置信度: {rec.get('confidence', 0.5):.0%}\n"
                    response_text += f"理由: {rec.get('reasoning', '暂无')[:300]}\n"
                    if rec.get('risk_assessment'):
                        response_text += f"风险等级: {rec['risk_assessment'].get('overall_risk', 'unknown')}"
                    return ChatResponse(response=response_text, related_stocks=[symbol])
                except Exception as e:
                    logger.warning(f"分析股票失败，使用规则引擎兜底: {e}")
                    return ChatResponse(response=self._rule_based_fallback(message, symbol))

        # 通用对话 - 先尝试LLM，失败则用规则引擎兜底
        try:
            if llm_service.is_available():
                response_text = await llm_service.generate(
                    system_prompt="你是FinAgent Pro金融数字员工，专业、友好、准确。用中文回答金融相关问题。",
                    user_prompt=message,
                )
                if response_text:
                    return ChatResponse(response=response_text)
        except Exception as e:
            logger.warning(f"LLM对话失败，使用规则引擎兜底: {e}")

        # 规则引擎兜底
        return ChatResponse(response=self._rule_based_fallback(message))

    async def _classify_intent(self, message: str) -> str:
        """分类用户意图"""
        msg = message.lower()
        if any(kw in msg for kw in ["分析", "怎么样", "看看", "评价"]) and self._extract_symbol(message):
            return "analyze_stock"
        if any(kw in msg for kw in ["市场", "大盘", "指数", "行情"]):
            return "market_overview"
        if any(kw in msg for kw in ["风险", "止损", "预警", "合规"]):
            return "risk_check"

        if not llm_service.is_available():
            return "general"

        try:
            result = await llm_service.generate_structured(
                system_prompt="分类用户意图",
                user_prompt=f"将以下用户消息分类为: analyze_stock(分析股票), market_overview(市场概览), risk_check(风险检查), general(通用对话)\n消息: {message}",
                output_schema={
                    "type": "object",
                    "properties": {"intent": {"type": "string"}}
                }
            )
            return result.get("intent", "general")
        except:
            return "general"

    def _rule_based_fallback(self, message: str, symbol: str = None) -> str:
        """规则引擎兜底回复 - 当LLM不可用时根据消息内容生成回复"""
        msg_lower = message.lower()

        # 股票分析相关
        if symbol:
            return (
                f"📊 {symbol} 快速参考:\n\n"
                f"目前LLM服务暂不可用，无法提供深度分析。您可以:\n"
                f"1. 稍后再试获取完整分析报告\n"
                f"2. 在分析页面输入股票代码获取技术指标\n"
                f"3. 查看市场概览了解大盘走势\n\n"
                f"温馨提示: 投资有风险，决策需谨慎。"
            )

        # 市场概览
        if any(kw in msg_lower for kw in ["市场", "大盘", "指数", "行情", "market"]):
            return (
                "📈 市场概览:\n\n"
                "目前LLM服务暂不可用，无法获取实时市场解读。建议您:\n"
                "1. 在市场概览页面查看主要指数走势\n"
                "2. 关注上证指数、深证成指、创业板指\n"
                "3. 稍后再试获取AI市场分析\n\n"
                "温馨提示: 市场波动属正常现象，请理性看待。"
            )

        # 风险相关
        if any(kw in msg_lower for kw in ["风险", "止损", "预警", "risk", "var"]):
            return (
                "⚠️ 风险提示:\n\n"
                "目前LLM服务暂不可用，无法进行深度风险评估。基本风控建议:\n"
                "1. 单只股票仓位不超过总资金的20%\n"
                "2. 设置止损线，建议亏损5%-8%止损\n"
                "3. 分散投资，避免集中持仓\n"
                "4. 关注市场系统性风险\n\n"
                "请在风控页面查看详细风险评估。"
            )

        # 通用兜底
        return (
            "您好！我是FinAgent Pro金融数字员工。\n\n"
            "目前AI服务暂时不可用，但我仍然可以帮您:\n"
            "1. 输入股票代码(如600519)进行技术分析\n"
            "2. 查看市场概览和实时行情\n"
            "3. 查看风险预警和持仓监控\n\n"
            "请稍后再试，或使用上方功能页面获取服务。"
        )

    def _extract_symbol(self, message: str) -> Optional[str]:
        """从消息中提取股票代码"""
        import re
        # 6位数字股票代码
        match = re.search(r'\b(\d{6})\b', message)
        if match:
            return match.group(1)
        # 常见股票名称映射
        stock_names = {
            "贵州茅台": "600519", "茅台": "600519",
            "宁德时代": "300750", "宁德": "300750",
            "比亚迪": "002594", "平安": "601318",
            "招商银行": "600036", "招行": "600036",
            "中国平安": "601318", "腾讯": "00700",
        }
        for name, code in stock_names.items():
            if name in message:
                return code
        return None

    def _generate_recommendation(self, symbol: str, stock_data: Dict, agent_results: Dict[str, AgentResult]) -> InvestmentRecommendation:
        """生成最终投资建议（多智能体协商）"""
        signals = []
        confidences = []
        key_findings = []
        risk_factors = []
        risk_assessment = None

        for name, result in agent_results.items():
            if result.signal and result.signal != SignalType.HOLD:
                signals.append(self._signal_to_numeric(result.signal))
            elif result.signal:
                signals.append(self._signal_to_numeric(result.signal))
            if result.confidence:
                confidences.append(result.confidence)
            key_findings.extend(result.key_findings[:3])
            risk_factors.extend(result.risk_factors[:2])

        # 加权平均信号
        if signals and confidences:
            weighted_signal = sum(s * c for s, c in zip(signals, confidences)) / sum(confidences)
            avg_confidence = sum(confidences) / len(confidences)
        else:
            weighted_signal = 0
            avg_confidence = 0.5

        final_signal = self._numeric_to_signal(weighted_signal)

        # 目标价和止损
        current_price = stock_data.get("current_price", 0)
        market_result = agent_results.get("market")
        atr = 0
        if market_result and market_result.metadata:
            atr = market_result.metadata.get("atr_14", current_price * 0.02)
        if not atr:
            atr = current_price * 0.02

        target_price = round(current_price + atr * 3, 2)
        stop_loss = round(current_price - atr * 2, 2)

        # 风险评估
        risk_result = agent_results.get("risk")
        if risk_result:
            risk_level_str = risk_result.metadata.get("overall_risk", "medium") if risk_result.metadata else "medium"
            # 将字符串转换为RiskLevel枚举
            try:
                from models.schemas import RiskLevel
                risk_level_enum = RiskLevel(risk_level_str)
            except ValueError:
                risk_level_enum = RiskLevel.MEDIUM
            risk_assessment = RiskAssessment(
                overall_risk=risk_level_enum,
                risk_score=risk_result.metadata.get("risk_score", 0.5) if risk_result.metadata else 0.5,
            )

        # 合规检查
        compliance_check = None
        if risk_result and risk_result.metadata and "compliance" in risk_result.metadata:
            compliance_check = risk_result.metadata["compliance"]

        reasoning = self._generate_reasoning(final_signal, agent_results, key_findings, risk_factors)

        return InvestmentRecommendation(
            symbol=symbol,
            company_name=stock_data.get("name", ""),
            signal=final_signal,
            confidence=round(avg_confidence, 2),
            target_price=target_price,
            stop_loss=stop_loss,
            reasoning=reasoning,
            key_points=key_findings[:5],
            risk_assessment=risk_assessment,
            compliance_check=compliance_check,
        )

    async def _llm_negotiate(self, symbol: str, stock_data: Dict, agent_results: Dict[str, AgentResult],
                              recommendation: InvestmentRecommendation) -> Optional[str]:
        """LLM多智能体协商增强"""
        context_parts = [f"股票: {symbol} ({stock_data.get('name', '')})"]
        context_parts.append(f"当前价: ¥{stock_data.get('current_price', 'N/A')}")

        for name, result in agent_results.items():
            context_parts.append(f"\n{name}智能体: 信号={result.signal}, 置信度={result.confidence}")
            if result.analysis:
                context_parts.append(f"分析: {result.analysis[:200]}")

        context_parts.append(f"\n初步建议: {recommendation.signal} (置信度{recommendation.confidence})")

        result = await llm_service.generate_structured(
            system_prompt="你是资深金融分析师，综合多个AI智能体的分析结果，生成专业投资建议。用中文回答。",
            user_prompt="\n".join(context_parts),
            output_schema={
                "type": "object",
                "properties": {
                    "reasoning": {"type": "string"},
                    "key_catalysts": {"type": "array", "items": {"type": "string"}},
                    "key_risks": {"type": "array", "items": {"type": "string"}},
                    "time_horizon": {"type": "string"}
                }
            }
        )

        reasoning = result.get("reasoning", "")
        if reasoning:
            catalysts = result.get("key_catalysts", [])
            risks = result.get("key_risks", [])
            horizon = result.get("time_horizon", "")
            if catalysts:
                reasoning += "\n\n关键催化剂:\n" + "\n".join(f"  {i+1}. {c}" for i, c in enumerate(catalysts[:3]))
            if risks:
                reasoning += "\n\n关键风险:\n" + "\n".join(f"  {i+1}. {r}" for i, r in enumerate(risks[:3]))
            if horizon:
                reasoning += f"\n\n建议持有周期: {horizon}"
        return reasoning

    def _generate_reasoning(self, signal: SignalType, agent_results: Dict, findings: List, risks: List) -> str:
        """生成规则引擎推理文本"""
        signal_names = {"strong_buy": "强烈买入", "buy": "买入", "hold": "持有", "sell": "卖出", "strong_sell": "强烈卖出"}
        reasoning = f"基于{len(agent_results)}个专业智能体的综合分析，建议: {signal_names.get(signal, '持有')}。\n\n"

        if findings:
            reasoning += "支撑因素:\n"
            for i, f in enumerate(findings[:3], 1):
                reasoning += f"  {i}. {f}\n"

        if risks:
            reasoning += "\n风险提示:\n"
            for i, r in enumerate(risks[:3], 1):
                reasoning += f"  {i}. {r}\n"

        return reasoning

    def _signal_to_numeric(self, signal: SignalType) -> float:
        return {"strong_buy": 1.0, "buy": 0.5, "hold": 0, "sell": -0.5, "strong_sell": -1.0}.get(signal, 0)

    def _numeric_to_signal(self, value: float) -> SignalType:
        if value > 0.5: return SignalType.STRONG_BUY
        if value > 0.2: return SignalType.BUY
        if value < -0.5: return SignalType.STRONG_SELL
        if value < -0.2: return SignalType.SELL
        return SignalType.HOLD

    def _map_agent_result(self, exec_result: Dict) -> AgentResult:
        """将智能体execute()返回的结果安全映射为AgentResult"""
        result_data = exec_result.get("result", {})
        # 安全提取字段，忽略AgentResult中不存在的key（如summary等）
        signal_str = result_data.get("signal", "hold")
        try:
            signal = SignalType(signal_str)
        except ValueError:
            signal = SignalType.HOLD

        return AgentResult(
            agent_name=exec_result.get("agent_name", ""),
            agent_type=exec_result.get("agent_type", ""),
            status=exec_result.get("status", "success"),
            signal=signal,
            confidence=result_data.get("confidence", 0.5),
            analysis=result_data.get("analysis", result_data.get("summary", "")),
            key_findings=result_data.get("key_findings", []),
            risk_factors=result_data.get("risk_factors", []),
            metadata=result_data.get("metadata", {}),
            llm_enhanced=result_data.get("llm_enhanced", False),
        )

    def get_agent_status(self) -> Dict[str, Any]:
        """获取所有智能体状态"""
        self._ensure_agents()
        return {name: agent.get_status() for name, agent in self.agents.items()}


# 单例
orchestrator = AgentOrchestrator()
