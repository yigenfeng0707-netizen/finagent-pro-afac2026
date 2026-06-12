"""新闻舆情智能体 - 中文金融新闻+社交媒体情绪+事件提取"""
import logging
from typing import Any, Dict, List
from .base_agent import BaseAgent
from .tools import register_news_tools
from .memory import get_agent_memory
from services.llm_service import llm_service

logger = logging.getLogger(__name__)


class NewsSentimentAgent(BaseAgent):
    """新闻舆情智能体：中文新闻抓取+情感分析+事件提取+社交情绪"""

    def __init__(self):
        super().__init__(
            name="新闻舆情智能体",
            agent_type="news",
            description="监控中文金融新闻、公司公告、社交媒体情绪，提取关键金融事件，评估舆情对股价的影响",
            max_steps=6,
        )
        register_news_tools(self)
        self.memory = get_agent_memory("news")

    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        symbol = data.get("symbol", "")
        company_name = data.get("company_name", "")

        # 1. 获取新闻
        from services.news_service import news_service
        news_articles = await news_service.fetch_stock_news(symbol=symbol, company_name=company_name, limit=10)

        # 2. 获取公告
        announcements = await news_service.fetch_announcements(symbol=symbol, limit=5)

        # 3. 获取社交情绪
        social_sentiment = await news_service.fetch_social_sentiment(symbol)

        # 4. 分析新闻情绪分布
        sentiment_dist = {"positive": 0, "negative": 0, "neutral": 0}
        total_score = 0
        for article in news_articles:
            sentiment = article.get("sentiment", "neutral")
            sentiment_dist[sentiment] = sentiment_dist.get(sentiment, 0) + 1
            total_score += article.get("sentiment_score", 0)

        avg_sentiment = total_score / len(news_articles) if news_articles else 0

        # 5. 确定信号
        signal = self._determine_signal(avg_sentiment, sentiment_dist)
        confidence = min(0.5 + len(news_articles) * 0.05, 0.9)

        # 6. 生成分析
        analysis = self._generate_analysis(news_articles, sentiment_dist, avg_sentiment, social_sentiment)
        key_findings = self._extract_findings(news_articles, sentiment_dist, social_sentiment)
        risk_factors = self._extract_risks(news_articles)

        result = {
            "summary": analysis,
            "signal": signal,
            "confidence": round(confidence, 2),
            "analysis": analysis,
            "key_findings": key_findings,
            "risk_factors": risk_factors,
            "metadata": {
                "news_count": len(news_articles),
                "sentiment_score": round(avg_sentiment, 3),
                "sentiment_distribution": sentiment_dist,
                "social_sentiment": social_sentiment,
            }
        }

        # LLM增强
        if llm_service.is_available() and news_articles:
            headlines = [a.get("title", "") for a in news_articles[:5]]
            llm_result = await self._llm_analyze(
                system_prompt="你是专业金融新闻分析师，分析新闻对股价的影响。用中文回答。",
                user_prompt=f"股票: {symbol}({company_name})\n新闻标题: {headlines}\n情绪分布: {sentiment_dist}\n平均情绪: {avg_sentiment:.3f}\n社交情绪: {social_sentiment}",
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

        self.memory.record_episode("news_analysis", f"分析{symbol}舆情", result)
        return result

    def _determine_signal(self, avg_sentiment: float, dist: Dict) -> str:
        if avg_sentiment > 0.4: return "buy"
        if avg_sentiment > 0.15: return "hold"
        if avg_sentiment < -0.4: return "sell"
        if avg_sentiment < -0.15: return "hold"
        return "hold"

    def _generate_analysis(self, articles, dist, avg, social) -> str:
        total = len(articles)
        if total == 0: return "暂无相关新闻数据"
        pos = dist.get("positive", 0)
        neg = dist.get("negative", 0)
        tone = "偏正面" if avg > 0.15 else "偏负面" if avg < -0.15 else "中性"
        return f"分析{total}条新闻，情绪{tone}。正面{pos}条，负面{neg}条，平均情绪分{avg:.2f}。"

    def _extract_findings(self, articles, dist, social) -> List[str]:
        findings = []
        if dist.get("positive", 0) > 3: findings.append("正面新闻占多数，市场情绪乐观")
        if dist.get("negative", 0) > 3: findings.append("负面新闻较多，需关注风险")
        if articles:
            top = max(articles, key=lambda a: abs(a.get("sentiment_score", 0)))
            findings.append(f"最关键新闻: {top.get('title', '')[:60]}")
        if social and social.get("hot_score", 0) > 50: findings.append("社交媒体讨论热度较高")
        return findings[:5]

    def _extract_risks(self, articles) -> List[str]:
        risks = []
        for a in articles:
            if a.get("sentiment") == "negative" and a.get("sentiment_score", 0) < -0.3:
                risks.append(f"负面报道: {a.get('title', '')[:50]}")
        return risks[:3]
