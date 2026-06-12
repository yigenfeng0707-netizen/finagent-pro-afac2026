"""全面测试脚本 - 验证所有模块功能"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def test_llm_service():
    """测试LLM服务"""
    print("\n=== 测试LLM服务 ===")
    from services.llm_service import llm_service
    
    print(f"LLM可用: {llm_service.is_available()}")
    print(f"主提供商: {llm_service.provider}")
    print(f"提供商数量: {len(llm_service._providers)}")
    
    if not llm_service.is_available():
        print("❌ LLM服务不可用")
        return False
    
    # 测试简单生成
    try:
        result = await llm_service.generate(
            system_prompt="你是金融助手",
            user_prompt="简单介绍一下贵州茅台",
            max_tokens=100
        )
        print(f"✓ LLM生成测试: {result[:50] if result else '空结果'}...")
        return bool(result)
    except Exception as e:
        print(f"❌ LLM生成失败: {e}")
        return False

async def test_market_data():
    """测试市场数据服务"""
    print("\n=== 测试市场数据服务 ===")
    from services.market_data import market_data_service
    
    # 测试股票数据
    stock = await market_data_service.get_stock_data("600519")
    print(f"✓ 股票数据: {stock.get('name', 'N/A')} 价格: {stock.get('current_price', 'N/A')}")
    
    # 测试市场概览
    overview = await market_data_service.get_market_overview()
    indices = overview.get('indices', [])
    print(f"✓ 市场概览: {len(indices)}个指数")
    
    return True

async def test_agents():
    """测试智能体"""
    print("\n=== 测试智能体 ===")
    from agents.market_agent import MarketAnalysisAgent
    from agents.news_agent import NewsSentimentAgent
    from agents.risk_agent import RiskComplianceAgent
    from agents.strategy_agent import StrategyAgent
    from agents.report_agent import ReportAgent
    
    # 测试市场分析
    market_agent = MarketAnalysisAgent()
    result = await market_agent.execute({
        "symbol": "600519",
        "stock_data": {"symbol": "600519", "name": "贵州茅台", "current_price": 1800}
    })
    print(f"✓ 市场分析: status={result.get('status')}, signal={result.get('result', {}).get('signal')}")
    
    # 测试新闻分析
    news_agent = NewsSentimentAgent()
    result = await news_agent.execute({
        "symbol": "600519",
        "company_name": "贵州茅台"
    })
    print(f"✓ 新闻分析: status={result.get('status')}, news_count={result.get('result', {}).get('metadata', {}).get('news_count')}")
    
    # 测试风控
    risk_agent = RiskComplianceAgent()
    result = await risk_agent.execute({
        "symbol": "600519",
        "stock_data": {"symbol": "600519", "name": "贵州茅台", "current_price": 1800},
        "technical_data": {},
        "sentiment_data": {}
    })
    print(f"✓ 风控分析: status={result.get('status')}, risk={result.get('result', {}).get('metadata', {}).get('overall_risk')}")
    
    # 测试报告生成
    report_agent = ReportAgent()
    result = await report_agent.generate_report("morning_daily", "600519")
    print(f"✓ 报告生成: {result.get('title', 'N/A')}")
    
    return True

async def test_orchestrator():
    """测试编排器"""
    print("\n=== 测试编排器 ===")
    from agents.orchestrator import orchestrator
    
    result = await orchestrator.analyze_stock(
        symbol="600519",
        analysis_type="comprehensive",
        include_news=True,
        include_risk=True,
        include_strategy=False
    )
    
    print(f"✓ 分析结果: {result.get('symbol')} - {result.get('company_name')}")
    rec = result.get('recommendation', {})
    print(f"  信号: {rec.get('signal')}, 置信度: {rec.get('confidence')}")
    print(f"  智能体数量: {len(result.get('agent_results', {}))}")
    print(f"  处理时间: {result.get('processing_time')}s")
    
    return True

async def test_api_routes():
    """测试API路由"""
    print("\n=== 测试API路由 ===")
    from fastapi.testclient import TestClient
    from main import app
    
    client = TestClient(app)
    
    # 测试健康检查
    resp = client.get("/api/health")
    print(f"✓ 健康检查: {resp.status_code} - {resp.json()}")
    
    # 测试市场概览
    resp = client.get("/api/market/overview")
    print(f"✓ 市场概览: {resp.status_code} - {len(resp.json().get('indices', []))}个指数")
    
    # 测试股票数据
    resp = client.get("/api/stock/600519")
    print(f"✓ 股票数据: {resp.status_code} - {resp.json().get('name')}")
    
    # 测试智能体状态
    resp = client.get("/api/agents/status")
    print(f"✓ 智能体状态: {resp.status_code} - {len(resp.json())}个智能体")
    
    return True

async def main():
    """主测试流程"""
    print("=" * 60)
    print("FinAgent Pro 全面功能测试")
    print("=" * 60)
    
    tests = [
        ("LLM服务", test_llm_service),
        ("市场数据", test_market_data),
        ("智能体", test_agents),
        ("编排器", test_orchestrator),
        ("API路由", test_api_routes),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = await test_func()
            results.append((name, success))
        except Exception as e:
            print(f"❌ {name}测试异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    for name, success in results:
        status = "✓ 通过" if success else "❌ 失败"
        print(f"{status} - {name}")
    
    all_passed = all(success for _, success in results)
    print("\n" + ("=" * 60))
    if all_passed:
        print("✅ 所有测试通过！")
    else:
        print("⚠️ 部分测试失败，需要修复")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
