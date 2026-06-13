"""
金融智能体工具集
定义所有智能体可调用的工具
"""
import logging
from typing import Any, Dict, List, Optional
from functools import partial

logger = logging.getLogger(__name__)


# ===== 市场数据工具 =====

async def get_stock_quote(symbol: str) -> Dict[str, Any]:
    """获取A股实时行情"""
    from services.market_data import market_data_service
    return await market_data_service.get_stock_data(symbol)


async def get_stock_history(symbol: str, period: str = "6mo") -> Any:
    """获取股票历史数据"""
    from services.market_data import market_data_service
    return await market_data_service.get_historical_data(symbol, period)


async def calc_technical_indicators(symbol: str) -> Dict[str, Any]:
    """计算技术指标"""
    from services.market_data import market_data_service
    return await market_data_service.calculate_technical_indicators(symbol)


async def get_capital_flow(symbol: str) -> Dict[str, Any]:
    """获取资金流向"""
    from services.market_data import market_data_service
    return await market_data_service.get_capital_flow(symbol)


async def get_financial_data(symbol: str) -> Dict[str, Any]:
    """获取财务数据"""
    from services.market_data import market_data_service
    return await market_data_service.get_financial_data(symbol)


async def get_sector_comparison(sector: str, metric: str = "pe") -> Dict[str, Any]:
    """获取行业对比数据"""
    from services.market_data import market_data_service
    return await market_data_service.get_sector_comparison(sector, metric)


async def get_dragon_tiger(symbol: str = None, date: str = None) -> Dict[str, Any]:
    """获取龙虎榜数据"""
    from services.market_data import market_data_service
    return await market_data_service.get_dragon_tiger(symbol, date)


# ===== 新闻舆情工具 =====

async def fetch_financial_news(symbol: str = "", limit: int = 10) -> List[Dict]:
    """获取金融新闻"""
    from services.news_service import news_service
    return await news_service.fetch_stock_news(symbol=symbol, limit=limit)


async def fetch_announcements(symbol: str, limit: int = 10) -> List[Dict]:
    """获取公司公告"""
    from services.news_service import news_service
    return await news_service.fetch_announcements(symbol=symbol, limit=limit)


async def analyze_sentiment(text: str) -> Dict[str, Any]:
    """分析文本情感"""
    from services.news_service import news_service
    return news_service.analyze_sentiment(text)


async def fetch_social_sentiment(symbol: str) -> Dict[str, Any]:
    """获取社交情绪"""
    from services.news_service import news_service
    return await news_service.fetch_social_sentiment(symbol)


# ===== 风控合规工具 =====

async def check_compliance(symbol: str, action: str = "buy", portfolio: Dict = None) -> Dict[str, Any]:
    """合规检查"""
    from services.compliance_service import compliance_service
    return await compliance_service.check(symbol=symbol, action=action, portfolio=portfolio)


async def calc_var(symbol: str, confidence: float = 0.95, period: int = 1) -> Dict[str, Any]:
    """计算VaR(风险价值)"""
    from services.risk_service import risk_service
    return await risk_service.calculate_var(symbol, confidence, period)


async def check_concentration(portfolio: Dict) -> Dict[str, Any]:
    """检查持仓集中度"""
    from services.compliance_service import compliance_service
    return await compliance_service.check_concentration(portfolio)


# ===== 报告工具 =====

async def generate_chart_data(symbol: str, period: str = "6mo") -> Dict[str, Any]:
    """生成图表数据"""
    from services.market_data import market_data_service
    return await market_data_service.get_chart_data(symbol, period)


# ===== 工具注册辅助函数 =====

def register_market_tools(agent):
    """为智能体注册市场数据工具"""
    agent.register_tool(
        name="get_stock_quote",
        description="获取A股实时行情数据，包括价格、涨跌幅、成交量等",
        func=get_stock_quote,
        parameters={"symbol": {"type": "string", "description": "股票代码，如600519"}}
    )
    agent.register_tool(
        name="calc_technical_indicators",
        description="计算技术指标：RSI、MACD、KDJ、布林带、ATR等",
        func=calc_technical_indicators,
        parameters={"symbol": {"type": "string", "description": "股票代码"}}
    )
    agent.register_tool(
        name="get_capital_flow",
        description="获取个股资金流向数据，主力/散户资金进出",
        func=get_capital_flow,
        parameters={"symbol": {"type": "string", "description": "股票代码"}}
    )
    agent.register_tool(
        name="get_financial_data",
        description="获取公司财务数据：PE、PB、ROE、营收增长等",
        func=get_financial_data,
        parameters={"symbol": {"type": "string", "description": "股票代码"}}
    )
    agent.register_tool(
        name="get_sector_comparison",
        description="获取同行业估值/涨幅排名对比",
        func=get_sector_comparison,
        parameters={"sector": {"type": "string", "description": "行业名称，如白酒、银行"}, "metric": {"type": "string", "description": "对比指标，如pe、pb"}}
    )


def register_news_tools(agent):
    """为智能体注册新闻舆情工具"""
    agent.register_tool(
        name="fetch_financial_news",
        description="获取金融新闻，支持按股票代码筛选",
        func=fetch_financial_news,
        parameters={"symbol": {"type": "string", "description": "股票代码（可选）"}, "limit": {"type": "integer", "description": "新闻条数"}}
    )
    agent.register_tool(
        name="fetch_announcements",
        description="获取上市公司公告",
        func=fetch_announcements,
        parameters={"symbol": {"type": "string", "description": "股票代码"}, "limit": {"type": "integer", "description": "公告条数"}}
    )
    agent.register_tool(
        name="analyze_sentiment",
        description="分析文本情感倾向（正面/负面/中性）",
        func=analyze_sentiment,
        parameters={"text": {"type": "string", "description": "待分析文本"}}
    )
    agent.register_tool(
        name="fetch_social_sentiment",
        description="获取社交媒体（雪球/股吧）情绪数据",
        func=fetch_social_sentiment,
        parameters={"symbol": {"type": "string", "description": "股票代码"}}
    )


def register_risk_tools(agent):
    """为智能体注册风控合规工具"""
    agent.register_tool(
        name="check_compliance",
        description="合规检查：单股集中度、行业集中度、创业板限制等",
        func=check_compliance,
        parameters={"symbol": {"type": "string", "description": "股票代码"}, "action": {"type": "string", "description": "操作类型: buy/sell"}, "portfolio": {"type": "object", "description": "当前持仓"}}
    )
    agent.register_tool(
        name="calc_var",
        description="计算VaR(风险价值)，评估最大可能损失",
        func=calc_var,
        parameters={"symbol": {"type": "string", "description": "股票代码"}, "confidence": {"type": "number", "description": "置信度，默认0.95"}, "period": {"type": "integer", "description": "持有天数，默认1"}}
    )
    agent.register_tool(
        name="check_concentration",
        description="检查持仓集中度风险",
        func=check_concentration,
        parameters={"portfolio": {"type": "object", "description": "持仓数据"}}
    )


def register_report_tools(agent):
    """为智能体注册报告生成工具"""
    agent.register_tool(
        name="generate_morning_report",
        description="生成金融晨报，包含隔夜市场、今日关注、持仓变动、风险提示等章节",
        func=agent.generate_report,
        parameters={"report_type": {"type": "string", "description": "报告类型: morning_daily"}, "symbol": {"type": "string", "description": "股票代码（可选）"}}
    )
    agent.register_tool(
        name="generate_stock_research",
        description="生成个股研报，包含公司概况、财务分析、估值分析、投资建议等章节",
        func=agent.generate_report,
        parameters={"report_type": {"type": "string", "description": "报告类型: stock_research"}, "symbol": {"type": "string", "description": "股票代码"}}
    )
    agent.register_tool(
        name="generate_risk_weekly",
        description="生成风控周报，包含风险指标、预警事件、合规检查、下周关注等章节",
        func=agent.generate_report,
        parameters={"report_type": {"type": "string", "description": "报告类型: risk_weekly"}}
    )
    agent.register_tool(
        name="generate_portfolio_monthly",
        description="生成组合月报，包含业绩回顾、持仓分析、调仓建议、下月展望等章节",
        func=agent.generate_report,
        parameters={"report_type": {"type": "string", "description": "报告类型: portfolio_monthly"}}
    )
    agent.register_tool(
        name="generate_event_flash",
        description="生成事件快报，包含事件概述、影响分析、操作建议等章节",
        func=agent.generate_report,
        parameters={"report_type": {"type": "string", "description": "报告类型: event_flash"}}
    )


def register_execution_tools(agent):
    """为智能体注册执行监控工具"""
    agent.register_tool(
        name="morning_scan",
        description="晨间巡检：扫描市场指数、持仓变动、重大事件",
        func=agent._morning_scan,
        parameters={}
    )
    agent.register_tool(
        name="risk_scan",
        description="风险扫描：检查持仓风险，发现超阈值波动并触发预警",
        func=agent._risk_scan,
        parameters={"portfolio": {"type": "object", "description": "持仓数据"}}
    )
    agent.register_tool(
        name="price_alert",
        description="价格预警：监控个股价格波动，超过阈值时触发预警",
        func=agent._price_alert,
        parameters={"symbol": {"type": "string", "description": "股票代码"}, "threshold": {"type": "number", "description": "波动阈值，默认0.05(5%)"}}
    )
    agent.register_tool(
        name="news_monitor",
        description="新闻监控：监控重要新闻和公告，发现异常舆情时触发预警",
        func=agent._morning_scan,
        parameters={}
    )


def register_all_tools(agent):
    """为智能体注册所有工具"""
    register_market_tools(agent)
    register_news_tools(agent)
    register_risk_tools(agent)
