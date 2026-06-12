"""
智能体单元测试
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_market_agent_analyze():
    """测试市场分析智能体"""
    from agents.market_agent import MarketAnalysisAgent
    agent = MarketAnalysisAgent()

    # 模拟数据
    mock_stock_data = {
        "symbol": "600519",
        "name": "贵州茅台",
        "current_price": 1856.0,
        "change_percent": 1.2,
        "volume": 5000000,
        "pe_ratio": 28.5,
    }

    with patch("services.market_data.market_data_service") as mock_market:
        mock_market.calculate_technical_indicators = AsyncMock(return_value={
            "rsi_14": 55.0, "macd": 0.5, "macd_signal": 0.3,
            "sma_20": 1840.0, "atr_14": 25.0, "current_price": 1856.0
        })
        mock_market.get_financial_data = AsyncMock(return_value=mock_stock_data)
        mock_market.get_capital_flow = AsyncMock(return_value={"main_net_inflow": 1000000})

        with patch("services.llm_service.llm_service") as mock_llm:
            mock_llm.is_available.return_value = False

            result = await agent.analyze({"symbol": "600519", "stock_data": mock_stock_data})

            assert "signal" in result
            assert "confidence" in result
            assert "analysis" in result
            assert result["signal"] in ["strong_buy", "buy", "hold", "sell", "strong_sell"]
            assert 0 <= result["confidence"] <= 1


@pytest.mark.asyncio
async def test_news_agent_analyze():
    """测试新闻舆情智能体"""
    from agents.news_agent import NewsSentimentAgent
    agent = NewsSentimentAgent()

    with patch("services.news_service.news_service") as mock_news:
        mock_news.fetch_stock_news = AsyncMock(return_value=[
            {"title": "利好消息", "sentiment": "positive", "sentiment_score": 0.5},
            {"title": "中性消息", "sentiment": "neutral", "sentiment_score": 0},
        ])
        mock_news.fetch_announcements = AsyncMock(return_value=[])
        mock_news.fetch_social_sentiment = AsyncMock(return_value={"hot_score": 50})

        with patch("services.llm_service.llm_service") as mock_llm:
            mock_llm.is_available.return_value = False

            result = await agent.analyze({"symbol": "600519", "company_name": "贵州茅台"})

            assert "signal" in result
            assert "confidence" in result


@pytest.mark.asyncio
async def test_risk_agent_analyze():
    """测试风控合规智能体"""
    from agents.risk_agent import RiskComplianceAgent
    agent = RiskComplianceAgent()

    stock_data = {"symbol": "600519", "name": "贵州茅台", "current_price": 1856.0, "volume": 5000000, "beta": 1.2}
    technical_data = {"metadata": {"atr_14": 25.0}}
    sentiment_data = {"metadata": {"sentiment_score": 0.1}}

    with patch("services.llm_service.llm_service") as mock_llm:
        mock_llm.is_available.return_value = False

        result = await agent.analyze({
            "symbol": "600519",
            "stock_data": stock_data,
            "technical_data": technical_data,
            "sentiment_data": sentiment_data,
        })

        assert "signal" in result
        assert "metadata" in result
        assert "overall_risk" in result["metadata"]


@pytest.mark.asyncio
async def test_strategy_agent_analyze():
    """测试投资策略智能体"""
    from agents.strategy_agent import StrategyAgent
    agent = StrategyAgent()

    with patch("services.llm_service.llm_service") as mock_llm:
        mock_llm.is_available.return_value = False

        result = await agent.analyze({
            "symbol": "600519",
            "stock_data": {"current_price": 1856.0},
            "market_result": {"signal": "buy"},
            "risk_result": {"metadata": {"overall_risk": "medium"}},
        })

        assert "signal" in result
        assert "metadata" in result
        assert "position" in result["metadata"]


@pytest.mark.asyncio
async def test_report_agent_generate():
    """测试报告生成智能体"""
    from agents.report_agent import ReportAgent
    agent = ReportAgent()

    with patch("services.llm_service.llm_service") as mock_llm:
        mock_llm.is_available.return_value = False
        with patch("services.database_service.db_service") as mock_db:
            mock_db.save_report = AsyncMock()

            result = await agent.generate_report("morning_daily")

            assert "report_id" in result
            assert "report_type" in result
            assert result["report_type"] == "morning_daily"


@pytest.mark.asyncio
async def test_execution_agent_morning_scan():
    """测试执行监控智能体"""
    from agents.execution_agent import ExecutionAgent
    agent = ExecutionAgent()

    with patch("services.market_data.market_data_service") as mock_market:
        mock_market.get_market_overview = AsyncMock(return_value={
            "indices": [{"name": "上证指数", "change_percent": 0.5}]
        })

        result = await agent.analyze({"task_type": "morning_scan"})

        assert "summary" in result
        assert "signal" in result


def test_base_agent_tool_registration():
    """测试工具注册"""
    from agents.base_agent import BaseAgent

    class TestAgent(BaseAgent):
        async def analyze(self, data):
            return {"signal": "hold", "confidence": 0.5, "analysis": "", "key_findings": [], "risk_factors": []}

    agent = TestAgent(name="测试", agent_type="test")
    agent.register_tool("test_tool", "测试工具", lambda: "ok", {})

    assert "test_tool" in agent._tools
    assert agent.get_tool_descriptions().startswith("- test_tool")


def test_base_agent_status():
    """测试智能体状态"""
    from agents.base_agent import BaseAgent

    class TestAgent(BaseAgent):
        async def analyze(self, data):
            return {"signal": "hold", "confidence": 0.5, "analysis": "", "key_findings": [], "risk_factors": []}

    agent = TestAgent(name="测试", agent_type="test")
    status = agent.get_status()

    assert status["name"] == "测试"
    assert status["execution_count"] == 0
    assert not status["is_running"]
