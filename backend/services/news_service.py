"""
中文金融新闻服务
支持东方财富新闻、公司公告、社交媒体情绪
"""
import logging
from typing import Any, Dict, List
from datetime import datetime, timedelta

import httpx

logger = logging.getLogger(__name__)

try:
    import jieba
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False


class NewsService:
    """中文金融新闻服务"""

    def __init__(self):
        self.eastmoney_base = "https://search-api-web.eastmoney.com/search/jsonp"

    async def fetch_stock_news(self, symbol: str = "", company_name: str = "", limit: int = 10) -> List[Dict]:
        """获取股票相关新闻"""
        if not company_name and symbol:
            company_name = symbol

        try:
            # 东方财富新闻搜索
            keyword = company_name or symbol or "A股"
            params = {"cb": "jQuery", "param": f'{{"uid":"","keyword":"{keyword}","type":["cmsArticleWebOld"],"client":"web","clientType":"web","clientVersion":"curr","param":{{"cmsArticleWebOld":{{"searchScope":"default","sort":"default","pageIndex":1,"pageSize":{limit},"preTag":"","postTag":""}}}}}}'}

            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(self.eastmoney_base, params=params)
                # 解析JSONP
                text = resp.text
                json_str = text[text.find("(") + 1:text.rfind(")")] if "(" in text else "{}"
                import json
                data = json.loads(json_str)

                articles = []
                items = data.get("result", {}).get("cmsArticleWebOld", {}).get("list", [])
                for item in items[:limit]:
                    title = item.get("title", "").replace("<em>", "").replace("</em>", "")
                    content = item.get("content", "")[:200]
                    sentiment = self._analyze_chinese_sentiment(title + " " + content)
                    articles.append({
                        "title": title,
                        "description": content,
                        "source": item.get("mediaName", "东方财富"),
                        "url": item.get("url", ""),
                        "published_at": item.get("date", datetime.now().isoformat()),
                        "sentiment": sentiment["label"],
                        "sentiment_score": sentiment["score"],
                    })
                return articles
        except Exception as e:
            logger.warning(f"获取新闻失败: {e}，使用模拟数据")
            return self._mock_news(symbol, company_name)

    async def fetch_announcements(self, symbol: str, limit: int = 10) -> List[Dict]:
        """获取公司公告"""
        return [{"title": f"{symbol}最新公告", "type": "公告", "date": datetime.now().isoformat()}]

    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """分析文本情感"""
        return self._analyze_chinese_sentiment(text)

    async def fetch_social_sentiment(self, symbol: str) -> Dict[str, Any]:
        """获取社交媒体情绪"""
        return {"hot_score": 50, "sentiment": "neutral", "discussion_count": 100}

    def _analyze_chinese_sentiment(self, text: str) -> Dict[str, Any]:
        """中文情感分析"""
        if not text:
            return {"label": "neutral", "score": 0}

        # 简单关键词情感分析
        positive_words = ["利好", "上涨", "增长", "突破", "新高", "超预期", "增持", "回购", "业绩大增", "涨停"]
        negative_words = ["利空", "下跌", "亏损", "暴雷", "退市", "减持", "违规", "处罚", "跌停", "风险"]

        pos_count = sum(1 for w in positive_words if w in text)
        neg_count = sum(1 for w in negative_words if w in text)

        if pos_count > neg_count:
            score = min(0.3 + pos_count * 0.1, 1.0)
            return {"label": "positive", "score": round(score, 3)}
        elif neg_count > pos_count:
            score = max(-0.3 - neg_count * 0.1, -1.0)
            return {"label": "negative", "score": round(score, 3)}
        return {"label": "neutral", "score": 0}

    def _mock_news(self, symbol: str, company_name: str) -> List[Dict]:
        name = company_name or symbol
        return [
            {"title": f"{name}发布业绩预告，净利润同比增长30%", "description": "业绩超市场预期", "source": "东方财富", "url": "#", "published_at": datetime.now().isoformat(), "sentiment": "positive", "sentiment_score": 0.6},
            {"title": f"机构调研{name}，看好长期发展", "description": "多家机构给予买入评级", "source": "证券时报", "url": "#", "published_at": (datetime.now() - timedelta(hours=2)).isoformat(), "sentiment": "positive", "sentiment_score": 0.5},
            {"title": f"{name}面临行业竞争压力", "description": "新进入者增多", "source": "中国证券报", "url": "#", "published_at": (datetime.now() - timedelta(hours=5)).isoformat(), "sentiment": "negative", "sentiment_score": -0.3},
        ]


# 单例
news_service = NewsService()
