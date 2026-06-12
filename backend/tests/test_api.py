"""
API集成测试
"""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_health_check():
    """测试健康检查"""
    from main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/agents/status")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_analyze_endpoint():
    """测试分析接口"""
    from main import app
    transport = ASGITransport(app=app)

    with patch("agents.orchestrator.orchestrator") as mock_orch:
        mock_orch.analyze_stock = AsyncMock(return_value={
            "request_id": "test123",
            "symbol": "600519",
            "company_name": "贵州茅台",
            "current_price": 1856.0,
            "recommendation": {"signal": "buy", "confidence": 0.7},
            "agent_results": {},
            "processing_time": 2.5,
        })

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/analyze", json={
                "symbol": "600519",
                "analysis_type": "comprehensive",
            })
            assert response.status_code == 200
            data = response.json()
            assert data["symbol"] == "600519"


@pytest.mark.asyncio
async def test_chat_endpoint():
    """测试对话接口"""
    from main import app
    transport = ASGITransport(app=app)

    with patch("agents.orchestrator.orchestrator") as mock_orch:
        mock_orch.chat = AsyncMock(return_value={
            "response": "贵州茅台当前价格1856元，建议持有。",
            "agent_steps": [],
            "related_stocks": ["600519"],
            "suggestions": [],
            "confidence": 0.7,
        })

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/chat", json={"message": "分析一下贵州茅台"})
            assert response.status_code == 200


@pytest.mark.asyncio
async def test_market_overview():
    """测试市场概览接口"""
    from main import app
    transport = ASGITransport(app=app)

    with patch("services.market_data.market_data_service") as mock_market:
        mock_market.get_market_overview = AsyncMock(return_value={
            "indices": [{"name": "上证指数", "current_price": 3200, "change_percent": 0.5}],
        })

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/market/overview")
            assert response.status_code == 200
