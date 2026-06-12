"""
服务层单元测试
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_market_data_service_mock():
    """测试市场数据服务（模拟模式）"""
    from services.market_data import MarketDataService
    service = MarketDataService()

    # 模拟模式下应返回模拟数据
    result = await service.get_stock_data("600519")
    assert "symbol" in result
    assert result["symbol"] == "600519"
    assert "current_price" in result


@pytest.mark.asyncio
async def test_market_data_service_chart():
    """测试K线图数据"""
    from services.market_data import MarketDataService
    service = MarketDataService()

    result = await service.get_chart_data("600519")
    assert "status" in result


@pytest.mark.asyncio
async def test_news_service_sentiment():
    """测试新闻情感分析"""
    from services.news_service import NewsService
    service = NewsService()

    # 正面
    pos = service.analyze_sentiment("利好消息，业绩大增，涨停")
    assert pos["label"] == "positive"

    # 负面
    neg = service.analyze_sentiment("利空消息，暴雷，跌停")
    assert neg["label"] == "negative"

    # 中性
    neu = service.analyze_sentiment("公司发布日常公告")
    assert neu["label"] == "neutral"


@pytest.mark.asyncio
async def test_compliance_service():
    """测试合规服务"""
    from services.compliance_service import ComplianceService
    service = ComplianceService()

    # ST股检查
    result = await service.check("002000", action="buy", portfolio={"name": "*ST某某"})
    assert not result["passed"]

    # 创业板检查
    result = await service.check("300750", action="buy")
    assert len(result["warnings"]) > 0

    # 正常股票
    result = await service.check("600519", action="buy")
    assert result["passed"]


@pytest.mark.asyncio
async def test_risk_service_var():
    """测试VaR计算"""
    from services.risk_service import RiskService
    service = RiskService()

    with patch("services.market_data.market_data_service") as mock_market:
        import pandas as pd
        import numpy as np
        dates = pd.date_range(end="2024-01-01", periods=120, freq="D")
        np.random.seed(42)
        prices = 100 * (1 + np.random.normal(0.0005, 0.02, 120)).cumprod()
        mock_df = pd.DataFrame({"Close": prices}, index=dates)
        mock_market.get_historical_data = AsyncMock(return_value=mock_df)

        result = await service.calculate_var("600519")
        assert "var" in result
        assert "confidence" in result


def test_llm_service_validation():
    """测试LLM结果验证"""
    from services.llm_service import LLMService

    # 信号验证
    result = LLMService.validate_agent_result({"signal": "买入"})
    assert result["signal"] == "buy"

    # 置信度截断
    result = LLMService.validate_agent_result({"confidence": 1.5})
    assert result["confidence"] == 1.0

    result = LLMService.validate_agent_result({"confidence": -0.5})
    assert result["confidence"] == 0.0


def test_memory_system():
    """测试记忆系统"""
    from agents.memory import AgentMemory, get_agent_memory

    memory = get_agent_memory("test")

    # 工作记忆
    memory.add_working("price", 1856.0)
    assert memory.get_working("price") == 1856.0

    # 情节记忆
    memory.record_episode("test", "测试任务", {"result": "ok"})
    episodes = memory.get_similar_experience("test")
    assert len(episodes) == 1

    # 语义记忆
    results = memory.query_knowledge("RSI")
    assert len(results) > 0

    # LLM上下文
    ctx = memory.get_context_for_llm()
    assert isinstance(ctx, str)


def test_database_service():
    """测试数据库服务"""
    from services.database_service import DatabaseService
    service = DatabaseService()

    # 内存存储测试
    import asyncio
    asyncio.run(service.save_analysis({"symbol": "600519"}))
    asyncio.run(service.save_alert({"alert_type": "price", "severity": "high", "title": "测试预警"}))
    asyncio.run(service.save_report({"report_type": "morning_daily", "title": "晨报"}))

    alerts = asyncio.run(service.get_alerts())
    assert len(alerts) >= 1

    reports = asyncio.run(service.get_reports())
    assert len(reports) >= 1
