"""
金融新闻服务
支持多数据源：东方财富(A股) + Finnhub(全球) + AKShare(国内)
自动降级：真实数据 → 缓存 → Mock数据
"""
import logging
import time
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

import httpx

from config import FINNHUB_API_KEY

logger = logging.getLogger(__name__)

# 尝试导入数据源
try:
    import finnhub
    _FH_AVAILABLE = bool(FINNHUB_API_KEY)
except ImportError:
    _FH_AVAILABLE = False

try:
    import akshare as ak
    _AK_AVAILABLE = True
except ImportError:
    _AK_AVAILABLE = False


class NewsService:
    """金融新闻服务 - 多数据源 + 自动降级"""

    def __init__(self):
        self.cache = {}
        self.cache_ts = {}
        self.cache_ttl = 60  # 新闻缓存60秒
        self.eastmoney_base = "https://search-api-web.eastmoney.com/search/jsonp"

    def _get_cached(self, key: str) -> Optional[Any]:
        if key in self.cache and key in self.cache_ts:
            if time.time() - self.cache_ts[key] < self.cache_ttl:
                return self.cache[key]
        return None

    def _set_cache(self, key: str, value: Any):
        self.cache[key] = value
        self.cache_ts[key] = time.time()

    async def fetch_stock_news(self, symbol: str = "", company_name: str = "", limit: int = 10) -> List[Dict]:
        """获取股票相关新闻 - 多数据源自动降级"""
        cache_key = f"news_{symbol}_{company_name}_{limit}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        if not company_name and symbol:
            company_name = symbol

        articles = []

        # 数据源1: Finnhub（全球新闻，海外服务器可用）
        if _FH_AVAILABLE:
            try:
                fh_news = await self._fetch_finnhub_news(symbol, limit)
                if fh_news:
                    articles.extend(fh_news)
            except Exception as e:
                logger.warning(f"Finnhub新闻获取失败: {e}")

        # 数据源2: 东方财富（A股新闻，国内可用）
        if len(articles) < limit:
            try:
                em_news = await self._fetch_eastmoney_news(company_name or symbol or "A股", limit - len(articles))
                if em_news:
                    articles.extend(em_news)
            except Exception as e:
                logger.warning(f"东方财富新闻获取失败: {e}")

        # 数据源3: AKShare新闻（A股）
        if len(articles) < limit and _AK_AVAILABLE:
            try:
                ak_news = await self._fetch_akshare_news(symbol, limit - len(articles))
                if ak_news:
                    articles.extend(ak_news)
            except Exception as e:
                logger.warning(f"AKShare新闻获取失败: {e}")

        # 降级到Mock
        if not articles:
            articles = self._mock_news(symbol, company_name)

        result = articles[:limit]
        self._set_cache(cache_key, result)
        return result

    async def _fetch_finnhub_news(self, symbol: str, limit: int) -> List[Dict]:
        """Finnhub获取全球金融新闻"""
        try:
            fh_client = finnhub.Client(api_key=FINNHUB_API_KEY)
            from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            to_date = datetime.now().strftime("%Y-%m-%d")

            if symbol and not symbol.isdigit():
                # 海外股票新闻
                raw = fh_client.company_news(symbol, _from=from_date, to=to_date)
            else:
                # 通用市场新闻
                raw = fh_client.general_news("general", min_id=0)

            if not raw:
                return []

            articles = []
            for item in raw[:limit]:
                title = item.get("headline", "")
                summary = item.get("summary", "")[:200]
                sentiment = self._analyze_chinese_sentiment(title + " " + summary)
                articles.append({
                    "title": title,
                    "description": summary,
                    "source": item.get("source", "Finnhub"),
                    "url": item.get("url", ""),
                    "published_at": datetime.fromtimestamp(item.get("datetime", 0)).isoformat() if item.get("datetime") else datetime.now().isoformat(),
                    "sentiment": sentiment["label"],
                    "sentiment_score": sentiment["score"],
                    "related_symbols": item.get("related", ""),
                })
            return articles
        except Exception as e:
            logger.warning(f"Finnhub新闻获取异常: {e}")
            return []

    async def _fetch_eastmoney_news(self, keyword: str, limit: int) -> List[Dict]:
        """东方财富获取A股新闻"""
        try:
            params = {"cb": "jQuery", "param": f'{{"uid":"","keyword":"{keyword}","type":["cmsArticleWebOld"],"client":"web","clientType":"web","clientVersion":"curr","param":{{"cmsArticleWebOld":{{"searchScope":"default","sort":"default","pageIndex":1,"pageSize":{limit},"preTag":"","postTag":""}}}}}}'}

            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(self.eastmoney_base, params=params)
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
            logger.warning(f"东方财富新闻获取异常: {e}")
            return []

    async def _fetch_akshare_news(self, symbol: str, limit: int) -> List[Dict]:
        """AKShare获取A股新闻/公告"""
        try:
            # 尝试获取个股新闻
            if symbol and symbol.isdigit():
                df = ak.stock_news_em(symbol=symbol)
                if df is not None and not df.empty:
                    articles = []
                    for _, row in df.head(limit).iterrows():
                        title = str(row.get("新闻标题", ""))
                        content = str(row.get("新闻内容", ""))[:200]
                        sentiment = self._analyze_chinese_sentiment(title + " " + content)
                        articles.append({
                            "title": title,
                            "description": content,
                            "source": str(row.get("文章来源", "AKShare")),
                            "url": str(row.get("新闻链接", "")),
                            "published_at": str(row.get("发布时间", datetime.now().isoformat())),
                            "sentiment": sentiment["label"],
                            "sentiment_score": sentiment["score"],
                        })
                    return articles
            return []
        except Exception as e:
            logger.warning(f"AKShare新闻获取异常: {e}")
            return []

    async def fetch_announcements(self, symbol: str, limit: int = 10) -> List[Dict]:
        """获取公司公告"""
        # 尝试AKShare
        if _AK_AVAILABLE and symbol and symbol.isdigit():
            try:
                df = ak.stock_notice_report(symbol=symbol)
                if df is not None and not df.empty:
                    announcements = []
                    for _, row in df.head(limit).iterrows():
                        announcements.append({
                            "title": str(row.get("公告标题", f"{symbol}公告")),
                            "type": str(row.get("公告类型", "公告")),
                            "date": str(row.get("公告日期", datetime.now().isoformat())),
                        })
                    return announcements
            except Exception as e:
                logger.warning(f"AKShare公告获取失败: {e}")

        # Finnhub公司新闻作为公告补充
        if _FH_AVAILABLE and symbol:
            try:
                fh_client = finnhub.Client(api_key=FINNHUB_API_KEY)
                from_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
                to_date = datetime.now().strftime("%Y-%m-%d")
                raw = fh_client.company_news(symbol, _from=from_date, to=to_date)
                if raw:
                    return [{
                        "title": item.get("headline", ""),
                        "type": "公司新闻",
                        "date": datetime.fromtimestamp(item.get("datetime", 0)).isoformat() if item.get("datetime") else datetime.now().isoformat(),
                    } for item in raw[:limit]]
            except Exception as e:
                logger.warning(f"Finnhub公告获取失败: {e}")

        return [{"title": f"{symbol}最新公告", "type": "公告", "date": datetime.now().isoformat()}]

    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """分析文本情感"""
        return self._analyze_chinese_sentiment(text)

    async def fetch_social_sentiment(self, symbol: str) -> Dict[str, Any]:
        """获取社交媒体情绪 - Finnhub情绪指标"""
        # Finnhub情绪数据
        if _FH_AVAILABLE and symbol and not symbol.isdigit():
            try:
                fh_client = finnhub.Client(api_key=FINNHUB_API_KEY)
                sentiment = fh_client.stock_social_sentiment(symbol)
                if sentiment and sentiment.get("reddit"):
                    reddit = sentiment["reddit"]
                    if isinstance(reddit, list) and reddit:
                        latest = reddit[-1] if reddit else {}
                        return {
                            "hot_score": latest.get("score", 50),
                            "sentiment": "positive" if latest.get("score", 0) > 0 else "negative",
                            "discussion_count": latest.get("comment", 0),
                            "source": "finnhub",
                        }
            except Exception as e:
                logger.warning(f"Finnhub社交情绪获取失败: {e}")

        return {"hot_score": 50, "sentiment": "neutral", "discussion_count": 100}

    def _analyze_chinese_sentiment(self, text: str) -> Dict[str, Any]:
        """中文+英文情感分析"""
        if not text:
            return {"label": "neutral", "score": 0}

        # 中文关键词
        positive_words = ["利好", "上涨", "增长", "突破", "新高", "超预期", "增持", "回购", "业绩大增", "涨停",
                          "surge", "rally", "gain", "beat", "upgrade", "bullish", "soar", "jump"]
        negative_words = ["利空", "下跌", "亏损", "暴雷", "退市", "减持", "违规", "处罚", "跌停", "风险",
                          "plunge", "crash", "drop", "miss", "downgrade", "bearish", "fall", "slump"]

        text_lower = text.lower()
        pos_count = sum(1 for w in positive_words if w in text_lower)
        neg_count = sum(1 for w in negative_words if w in text_lower)

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
