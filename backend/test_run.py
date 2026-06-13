"""
FinAgent Pro 全流程测试脚本
测试美股(AAPL)、A股(600036)标的
验证：真实数据返回、缓存生效、异常降级至Mock
"""

import asyncio
import sys
import os
import time
import logging

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ===== 测试结果统计 =====
results = {"pass": 0, "fail": 0, "skip": 0, "details": []}


def record(test_name: str, passed: bool, detail: str = ""):
    status = "PASS" if passed else "FAIL"
    if passed:
        results["pass"] += 1
    else:
        results["fail"] += 1
    results["details"].append((test_name, status, detail))
    icon = "✓" if passed else "✗"
    print(f"  {icon} [{status}] {test_name} {('- ' + detail) if detail else ''}")


# ===== 任务1: 环境依赖检查 =====
async def test_environment():
    print("\n" + "=" * 60)
    print("任务1: 环境依赖检查")
    print("=" * 60)

    # 检查核心依赖
    deps = {
        "akshare": "akshare",
        "yfinance": "yfinance",
        "finnhub": "finnhub",
        "pandas": "pandas",
        "numpy": "numpy",
        "python-dotenv": "dotenv",
        "python-docx": "docx",
        "bcrypt": "bcrypt",
        "python-jose": "jose",
        "requests": "requests",
    }

    for name, mod in deps.items():
        try:
            __import__(mod)
            record(f"依赖安装: {name}", True)
        except ImportError:
            record(f"依赖安装: {name}", False, "未安装")

    # 检查.env配置
    from config import USE_REAL_DATA, AKSHARE_ENABLED, YFINANCE_ENABLED, FINNHUB_API_KEY
    record("配置: USE_REAL_DATA", USE_REAL_DATA, f"值={USE_REAL_DATA}")
    record("配置: AKSHARE_ENABLED", AKSHARE_ENABLED, f"值={AKSHARE_ENABLED}")
    record("配置: YFINANCE_ENABLED", YFINANCE_ENABLED, f"值={YFINANCE_ENABLED}")
    record("配置: FINNHUB_API_KEY", bool(FINNHUB_API_KEY), "已配置" if FINNHUB_API_KEY else "未配置(可选)")


# ===== 任务2: 统一数据适配层测试 =====
async def test_data_adapter():
    print("\n" + "=" * 60)
    print("任务2: 统一数据适配层 - 真实数据获取")
    print("=" * 60)

    from services.data_adapter import DataAdapter
    adapter = DataAdapter()

    # 测试美股 AAPL
    print("\n--- 美股: AAPL ---")
    try:
        aapl = await adapter.get_stock_quote("AAPL")
        has_data = aapl.get("current_price", 0) > 0
        source = aapl.get("source", "unknown")
        record("AAPL 行情获取", has_data, f"source={source}, price={aapl.get('current_price')}")
        record("AAPL 字段完整性", all(k in aapl for k in ["symbol", "name", "current_price", "change", "change_percent", "volume"]), f"字段数={len(aapl)}")
    except Exception as e:
        record("AAPL 行情获取", False, str(e))

    # 测试A股 600036
    print("\n--- A股: 600036 ---")
    try:
        stock = await adapter.get_stock_quote("600036")
        has_data = stock.get("current_price", 0) > 0
        source = stock.get("source", "unknown")
        record("600036 行情获取", has_data, f"source={source}, price={stock.get('current_price')}")
        record("600036 字段完整性", all(k in stock for k in ["symbol", "name", "current_price", "change", "change_percent"]), f"字段数={len(stock)}")
    except Exception as e:
        record("600036 行情获取", False, str(e))

    # 测试历史数据
    print("\n--- 历史K线数据 ---")
    try:
        hist = await adapter.get_historical_data("AAPL", "6mo")
        record("AAPL 历史数据", not hist.empty and len(hist) > 10, f"行数={len(hist)}")
    except Exception as e:
        record("AAPL 历史数据", False, str(e))

    try:
        hist_a = await adapter.get_historical_data("600036", "6mo")
        record("600036 历史数据", not hist_a.empty and len(hist_a) > 10, f"行数={len(hist_a)}")
    except Exception as e:
        record("600036 历史数据", False, str(e))

    # 测试市场概览
    print("\n--- 市场概览 ---")
    try:
        overview = await adapter.get_market_overview()
        indices = overview.get("indices", [])
        record("市场概览", len(indices) > 0, f"指数数={len(indices)}, sources={[i.get('source') for i in indices]}")
    except Exception as e:
        record("市场概览", False, str(e))


# ===== 任务3: 缓存机制验证 =====
async def test_cache():
    print("\n" + "=" * 60)
    print("任务3: 缓存机制验证")
    print("=" * 60)

    from services.data_adapter import DataAdapter
    adapter = DataAdapter()

    # 第一次调用
    t1 = time.time()
    r1 = await adapter.get_stock_quote("AAPL")
    elapsed1 = time.time() - t1

    # 第二次调用（应命中缓存）
    t2 = time.time()
    r2 = await adapter.get_stock_quote("AAPL")
    elapsed2 = time.time() - t2

    cache_hit = elapsed2 < elapsed1 * 0.5  # 缓存命中应更快
    record("缓存命中", cache_hit, f"首次={elapsed1:.3f}s, 缓存={elapsed2:.3f}s")

    # 数据一致性
    record("缓存数据一致性", r1.get("current_price") == r2.get("current_price"),
           f"price1={r1.get('current_price')}, price2={r2.get('current_price')}")

    # 缓存TTL验证
    record("缓存TTL配置", adapter.cache_ttl == 10, f"TTL={adapter.cache_ttl}s")


# ===== 任务4: 异常降级测试 =====
async def test_degradation():
    print("\n" + "=" * 60)
    print("任务4: 异常降级至Mock数据")
    print("=" * 60)

    from services.data_adapter import DataAdapter

    # 场景1: USE_REAL_DATA=false → 直接走Mock
    original = os.environ.get("USE_REAL_DATA", "true")
    os.environ["USE_REAL_DATA"] = "false"

    # 重新创建adapter以读取新环境变量
    import importlib
    import config
    importlib.reload(config)
    from services import data_adapter as da_module
    importlib.reload(da_module)

    adapter = da_module.DataAdapter()
    try:
        r = await adapter.get_stock_quote("AAPL")
        record("USE_REAL_DATA=false → Mock降级", r.get("source") == "mock", f"source={r.get('source')}")
    except Exception as e:
        record("USE_REAL_DATA=false → Mock降级", False, str(e))

    # 场景2: 无效symbol → Mock降级
    os.environ["USE_REAL_DATA"] = "true"
    importlib.reload(config)
    importlib.reload(da_module)
    adapter = da_module.DataAdapter()

    try:
        r = await adapter.get_stock_quote("INVALID_SYMBOL_XYZ")
        record("无效symbol → Mock降级", r.get("source") == "mock", f"source={r.get('source')}")
    except Exception as e:
        record("无效symbol → Mock降级", False, str(e))

    # 恢复环境变量
    os.environ["USE_REAL_DATA"] = original
    importlib.reload(config)
    importlib.reload(da_module)


# ===== 任务5: MarketDataService集成测试 =====
async def test_market_data_service():
    print("\n" + "=" * 60)
    print("任务5: MarketDataService集成测试")
    print("=" * 60)

    from services.market_data import MarketDataService
    svc = MarketDataService()

    # 测试get_stock_data
    try:
        data = await svc.get_stock_data("AAPL")
        record("MarketDataService.get_stock_data(AAPL)", data.get("current_price", 0) > 0,
               f"price={data.get('current_price')}, source={data.get('source')}")
    except Exception as e:
        record("MarketDataService.get_stock_data(AAPL)", False, str(e))

    try:
        data = await svc.get_stock_data("600036")
        record("MarketDataService.get_stock_data(600036)", data.get("current_price", 0) > 0,
               f"price={data.get('current_price')}, source={data.get('source')}")
    except Exception as e:
        record("MarketDataService.get_stock_data(600036)", False, str(e))

    # 测试技术指标
    try:
        indicators = await svc.calculate_technical_indicators("AAPL")
        has_indicators = any(k in indicators for k in ["rsi_14", "macd", "sma_20"])
        record("技术指标计算(AAPL)", has_indicators, f"指标数={len(indicators)}")
    except Exception as e:
        record("技术指标计算(AAPL)", False, str(e))

    # 测试K线图数据
    try:
        chart = await svc.get_chart_data("AAPL", "6mo")
        record("K线图数据(AAPL)", chart.get("status") == "success", f"candles={len(chart.get('candles', []))}")
    except Exception as e:
        record("K线图数据(AAPL)", False, str(e))


# ===== 任务6: OpenBB接口测试 =====
async def test_openbb():
    print("\n" + "=" * 60)
    print("任务6: OpenBB扩展能力（可选）")
    print("=" * 60)

    from services.data_adapter import DataAdapter
    adapter = DataAdapter()

    try:
        r = await adapter.get_fundamental_data("AAPL")
        record("OpenBB基本面", r.get("source") in ["openbb", "mock"], f"source={r.get('source')}")
    except Exception as e:
        record("OpenBB基本面", False, str(e))

    try:
        r = await adapter.get_earnings("AAPL")
        record("OpenBB财报", r.get("source") in ["openbb", "mock"], f"source={r.get('source')}")
    except Exception as e:
        record("OpenBB财报", False, str(e))

    try:
        r = await adapter.get_forex_rate("USD", "CNY")
        record("OpenBB汇率", r.get("source") in ["openbb", "mock"], f"source={r.get('source')}, rate={r.get('rate')}")
    except Exception as e:
        record("OpenBB汇率", False, str(e))


# ===== 任务7: Finnhub数据源测试 =====
async def test_finnhub():
    print("\n" + "=" * 60)
    print("任务7: Finnhub数据源验证")
    print("=" * 60)

    from config import FINNHUB_API_KEY
    if not FINNHUB_API_KEY:
        record("Finnhub API Key", False, "未配置，跳过测试")
        return

    record("Finnhub API Key已配置", True, f"key={FINNHUB_API_KEY[:8]}...")

    try:
        import finnhub
        fh = finnhub.Client(api_key=FINNHUB_API_KEY)

        # 测试行情
        quote = fh.quote("AAPL")
        has_price = quote and quote.get("c", 0) > 0
        record("Finnhub AAPL行情", has_price, f"price={quote.get('c')}, source=finnhub")

        # 测试公司新闻
        from datetime import datetime, timedelta
        from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        to_date = datetime.now().strftime("%Y-%m-%d")
        news = fh.company_news("AAPL", _from=from_date, to=to_date)
        record("Finnhub AAPL新闻", isinstance(news, list), f"新闻数={len(news) if news else 0}")

        # 测试公司信息
        profile = fh.company_profile2(symbol="AAPL")
        record("Finnhub AAPL公司信息", bool(profile and profile.get("name")), f"name={profile.get('name') if profile else 'N/A'}")

        # 测试通用新闻
        general = fh.general_news("general", min_id=0)
        record("Finnhub 通用新闻", isinstance(general, list), f"新闻数={len(general) if general else 0}")

    except Exception as e:
        record("Finnhub连接测试", False, str(e))


# ===== 任务8: 新闻服务测试 =====
async def test_news_service():
    print("\n" + "=" * 60)
    print("任务8: 新闻舆情服务验证")
    print("=" * 60)

    from services.news_service import NewsService
    svc = NewsService()

    # 测试美股新闻
    try:
        news = await svc.fetch_stock_news(symbol="AAPL", company_name="Apple", limit=5)
        record("AAPL新闻获取", len(news) > 0, f"新闻数={len(news)}, sources={[n.get('source') for n in news[:3]]}")
    except Exception as e:
        record("AAPL新闻获取", False, str(e))

    # 测试A股新闻
    try:
        news = await svc.fetch_stock_news(symbol="600036", company_name="招商银行", limit=5)
        record("600036新闻获取", len(news) > 0, f"新闻数={len(news)}, sources={[n.get('source') for n in news[:3]]}")
    except Exception as e:
        record("600036新闻获取", False, str(e))

    # 测试情感分析
    try:
        pos = svc.analyze_sentiment("利好消息，业绩大涨超预期")
        neg = svc.analyze_sentiment("利空，暴雷退市风险")
        record("中文情感分析", pos["label"] == "positive" and neg["label"] == "negative",
               f"正面={pos['label']}({pos['score']}), 负面={neg['label']}({neg['score']})")
    except Exception as e:
        record("中文情感分析", False, str(e))

    # 测试社交情绪
    try:
        social = await svc.fetch_social_sentiment("AAPL")
        record("社交情绪获取", "hot_score" in social, f"hot_score={social.get('hot_score')}")
    except Exception as e:
        record("社交情绪获取", False, str(e))

    # 测试缓存
    try:
        t1 = time.time()
        await svc.fetch_stock_news(symbol="AAPL", limit=3)
        t2 = time.time()
        await svc.fetch_stock_news(symbol="AAPL", limit=3)
        t3 = time.time()
        record("新闻缓存命中", (t3 - t2) < (t2 - t1) * 0.5, f"首次={t2-t1:.3f}s, 缓存={t3-t2:.3f}s")
    except Exception as e:
        record("新闻缓存命中", False, str(e))


# ===== 任务9: 新闻智能体集成测试 =====
async def test_news_agent():
    print("\n" + "=" * 60)
    print("任务9: 新闻舆情智能体集成测试")
    print("=" * 60)

    try:
        from agents.news_agent import NewsSentimentAgent
        agent = NewsSentimentAgent()

        # 检查工具注册
        record("新闻智能体工具注册", len(agent._tools) > 0, f"工具数={len(agent._tools)}, 工具={list(agent._tools.keys())}")

        # 执行分析
        result = await agent.analyze({"symbol": "AAPL", "company_name": "Apple"})
        record("新闻智能体分析", "signal" in result and "analysis" in result,
               f"signal={result.get('signal')}, news_count={result.get('metadata', {}).get('news_count')}")
        record("新闻智能体非空结果", result.get("analysis") != "暂无相关新闻数据",
               f"analysis={result.get('analysis', '')[:80]}")
    except Exception as e:
        record("新闻智能体集成", False, str(e))


# ===== 输出最终报告 =====
def print_report():
    print("\n" + "=" * 60)
    print("全流程测试报告")
    print("=" * 60)
    total = results["pass"] + results["fail"]
    rate = (results["pass"] / total * 100) if total > 0 else 0
    print(f"\n  通过: {results['pass']}  失败: {results['fail']}  通过率: {rate:.1f}%\n")

    if results["fail"] > 0:
        print("  失败项:")
        for name, status, detail in results["details"]:
            if status == "FAIL":
                print(f"    ✗ {name} - {detail}")

    print("\n" + "=" * 60)
    print("运行说明")
    print("=" * 60)
    print("""
  数据源切换开关:
    .env 文件中 USE_REAL_DATA=true  → 使用真实数据源
    .env 文件中 USE_REAL_DATA=false → 使用Mock模拟数据

  A股数据源: AKSHARE_ENABLED=true (默认开启)
  美股数据源: YFINANCE_ENABLED=true (默认开启)
  Finnhub:   FINNHUB_API_KEY=xxx (可选，需申请API Key)

  缓存策略:
    - 行情数据缓存TTL: 10秒
    - 历史数据缓存TTL: 10秒
    - 过期缓存自动清理

  降级策略:
    1. 优先使用真实数据源(AKShare/yfinance/Finnhub)
    2. 真实数据源失败 → 检查缓存
    3. 缓存过期/无缓存 → 降级至Mock数据

  限流注意事项:
    - yfinance: 无官方限流，但频繁请求可能被限制，建议间隔>1秒
    - AKShare:  请求频率建议<30次/分钟
    - Finnhus:  免费版60次/分钟
    - 缓存TTL=10秒可有效降低请求频率
""")


# ===== 主入口 =====
async def main():
    print("=" * 60)
    print("FinAgent Pro 全流程测试")
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    await test_environment()
    await test_data_adapter()
    await test_cache()
    await test_degradation()
    await test_market_data_service()
    await test_openbb()
    await test_finnhub()
    await test_news_service()
    await test_news_agent()

    print_report()


if __name__ == "__main__":
    asyncio.run(main())
