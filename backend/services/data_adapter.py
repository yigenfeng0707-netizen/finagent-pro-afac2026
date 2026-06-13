"""
统一金融数据适配层
支持多数据源：AKShare(A股) + yfinance(美股/海外) + Finnhub(全球)
自动降级：真实数据 → 缓存 → Mock数据
"""

import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import pandas as pd
import numpy as np

from config import USE_REAL_DATA, AKSHARE_ENABLED, YFINANCE_ENABLED, FINNHUB_API_KEY

logger = logging.getLogger(__name__)

# 尝试导入数据源
try:
    import akshare as ak
    _AK_AVAILABLE = True
except ImportError:
    _AK_AVAILABLE = False

try:
    import yfinance as yf
    _YF_AVAILABLE = True
except ImportError:
    _YF_AVAILABLE = False

try:
    import finnhub
    _FH_AVAILABLE = bool(FINNHUB_API_KEY)
except ImportError:
    _FH_AVAILABLE = False


class DataAdapter:
    """统一金融数据适配器"""

    def __init__(self):
        self.cache = {}
        self.cache_ts = {}
        self.cache_ttl = 10  # 10秒缓存

    def _get_cached(self, key: str) -> Optional[Any]:
        if key in self.cache and key in self.cache_ts:
            if time.time() - self.cache_ts[key] < self.cache_ttl:
                return self.cache[key]
        return None

    def _set_cache(self, key: str, value: Any):
        self.cache[key] = value
        self.cache_ts[key] = time.time()
        # 清理过期缓存
        now = time.time()
        expired = [k for k, t in self.cache_ts.items() if now - t > self.cache_ttl * 6]
        for k in expired:
            self.cache.pop(k, None)
            self.cache_ts.pop(k, None)

    async def get_stock_quote(self, symbol: str) -> Dict[str, Any]:
        """
        统一股票行情接口
        自动判断：6位数字→A股(AKShare)，否则→海外(yfinance/Finnhub)
        """
        cached = self._get_cached(f"quote_{symbol}")
        if cached:
            return cached

        result = None
        is_a_share = symbol.isdigit() and len(symbol) == 6

        if USE_REAL_DATA:
            if is_a_share and AKSHARE_ENABLED and _AK_AVAILABLE:
                result = await self._get_a_share_quote(symbol)
            elif not is_a_share and YFINANCE_ENABLED and _YF_AVAILABLE:
                result = await self._get_overseas_quote(symbol)

        # 降级到Mock
        if result is None:
            result = self._mock_stock_data(symbol)

        self._set_cache(f"quote_{symbol}", result)
        return result

    async def _get_a_share_quote(self, symbol: str) -> Optional[Dict]:
        """AKShare获取A股实时行情"""
        try:
            df = ak.stock_zh_a_spot_em()
            row = df[df['代码'] == symbol]
            if row.empty:
                return None
            r = row.iloc[0]
            return {
                "symbol": symbol,
                "name": str(r.get('名称', symbol)),
                "current_price": float(r.get('最新价', 0)) if pd.notna(r.get('最新价')) else 0,
                "change": float(r.get('涨跌额', 0)) if pd.notna(r.get('涨跌额')) else 0,
                "change_percent": float(r.get('涨跌幅', 0)) if pd.notna(r.get('涨跌幅')) else 0,
                "volume": int(r.get('成交量', 0)) if pd.notna(r.get('成交量')) else 0,
                "amount": float(r.get('成交额', 0)) if pd.notna(r.get('成交额')) else 0,
                "high": float(r.get('最高', 0)) if pd.notna(r.get('最高')) else 0,
                "low": float(r.get('最低', 0)) if pd.notna(r.get('最低')) else 0,
                "open": float(r.get('今开', 0)) if pd.notna(r.get('今开')) else 0,
                "prev_close": float(r.get('昨收', 0)) if pd.notna(r.get('昨收')) else 0,
                "market_cap": float(r.get('总市值', 0)) if pd.notna(r.get('总市值')) else None,
                "pe_ratio": float(r.get('市盈率-动态', 0)) if pd.notna(r.get('市盈率-动态')) else None,
                "pb_ratio": float(r.get('市净率', 0)) if pd.notna(r.get('市净率')) else None,
                "turnover_rate": float(r.get('换手率', 0)) if pd.notna(r.get('换手率')) else None,
                "source": "akshare",
            }
        except Exception as e:
            logger.warning(f"AKShare获取A股行情失败[{symbol}]: {e}")
            return None

    async def _get_overseas_quote(self, symbol: str) -> Optional[Dict]:
        """yfinance获取海外股票行情"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            if not info:
                return None
            price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
            prev = info.get('previousClose', 0)
            change = price - prev if price and prev else 0
            change_pct = (change / prev * 100) if prev else 0
            return {
                "symbol": symbol,
                "name": info.get('shortName', info.get('longName', symbol)),
                "current_price": round(float(price), 2) if price else 0,
                "change": round(float(change), 2),
                "change_percent": round(float(change_pct), 2),
                "volume": int(info.get('volume', 0)) or 0,
                "amount": 0,
                "high": round(float(info.get('dayHigh', 0)), 2),
                "low": round(float(info.get('dayLow', 0)), 2),
                "open": round(float(info.get('open', 0)), 2),
                "prev_close": round(float(prev), 2) if prev else 0,
                "market_cap": info.get('marketCap'),
                "pe_ratio": info.get('trailingPE'),
                "pb_ratio": info.get('priceToBook'),
                "turnover_rate": None,
                "source": "yfinance",
            }
        except Exception as e:
            logger.warning(f"yfinance获取海外行情失败[{symbol}]: {e}")
            return None

    async def get_historical_data(self, symbol: str, period: str = "6mo") -> pd.DataFrame:
        """获取历史K线数据"""
        cached = self._get_cached(f"hist_{symbol}_{period}")
        if cached is not None:
            return cached

        is_a_share = symbol.isdigit() and len(symbol) == 6
        df = None

        if USE_REAL_DATA:
            if is_a_share and AKSHARE_ENABLED and _AK_AVAILABLE:
                df = await self._get_a_share_history(symbol, period)
            elif not is_a_share and YFINANCE_ENABLED and _YF_AVAILABLE:
                df = self._get_overseas_history(symbol, period)

        if df is None or df.empty:
            df = self._mock_historical_data()

        self._set_cache(f"hist_{symbol}_{period}", df)
        return df

    async def _get_a_share_history(self, symbol: str, period: str) -> Optional[pd.DataFrame]:
        """AKShare获取A股历史数据"""
        try:
            period_map = {"1mo": "30", "3mo": "90", "6mo": "180", "1y": "365"}
            ak_period = period_map.get(period, "180")
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date="", end_date="", adjust="qfq")
            if df.empty:
                return None
            df = df.tail(int(ak_period))
            df = df.rename(columns={"日期": "Date", "开盘": "Open", "收盘": "Close", "最高": "High", "最低": "Low", "成交量": "Volume"})
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.set_index('Date')
            for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            return df
        except Exception as e:
            logger.warning(f"AKShare获取A股历史失败[{symbol}]: {e}")
            return None

    def _get_overseas_history(self, symbol: str, period: str) -> Optional[pd.DataFrame]:
        """yfinance获取海外历史数据"""
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period)
            if df.empty:
                return None
            df = df.rename(columns={"Open": "Open", "High": "High", "Low": "Low", "Close": "Close", "Volume": "Volume"})
            return df
        except Exception as e:
            logger.warning(f"yfinance获取海外历史失败[{symbol}]: {e}")
            return None

    async def get_market_overview(self) -> Dict[str, Any]:
        """获取市场概览"""
        cached = self._get_cached("market_overview")
        if cached:
            return cached

        indices = []
        if USE_REAL_DATA and AKSHARE_ENABLED and _AK_AVAILABLE:
            try:
                df = ak.stock_zh_index_spot_em()
                indices_map = {"000001": "上证指数", "399001": "深证成指", "399006": "创业板指"}
                for code, name in indices_map.items():
                    row = df[df['代码'] == code]
                    if not row.empty:
                        r = row.iloc[0]
                        indices.append({
                            "name": name,
                            "symbol": code,
                            "current_price": float(r.get('最新价', 0)),
                            "change_percent": float(r.get('涨跌幅', 0)),
                            "source": "akshare",
                        })
            except Exception as e:
                logger.warning(f"AKShare市场概览失败: {e}")

        if not indices:
            indices = self._mock_indices()

        result = {"indices": indices, "timestamp": datetime.now().isoformat()}
        self._set_cache("market_overview", result)
        return result

    async def get_financial_data(self, symbol: str) -> Dict[str, Any]:
        """获取财务数据"""
        return await self.get_stock_quote(symbol)

    async def get_capital_flow(self, symbol: str) -> Dict[str, Any]:
        """获取资金流向"""
        if USE_REAL_DATA and AKSHARE_ENABLED and _AK_AVAILABLE:
            try:
                df = ak.stock_individual_fund_flow(stock=symbol, market="sh" if symbol.startswith("6") else "sz")
                if not df.empty:
                    latest = df.iloc[-1]
                    return {
                        "main_net_inflow": float(latest.get('主力净流入-净额', 0)),
                        "retail_net_inflow": float(latest.get('散户净流入-净额', 0)),
                        "source": "akshare",
                    }
            except Exception as e:
                logger.warning(f"AKShare资金流向失败[{symbol}]: {e}")
        return {"main_net_inflow": 0, "retail_net_inflow": 0}

    # ===== OpenBB 可选接口 =====

    async def get_fundamental_data(self, symbol: str) -> Dict[str, Any]:
        """获取基本面数据（OpenBB可选）"""
        try:
            from openbb import obb
            data = obb.equity.fundamental.balance(symbol=symbol)
            return {"source": "openbb", "data": data.to_dict() if hasattr(data, 'to_dict') else {}}
        except Exception as e:
            logger.debug(f"OpenBB不可用: {e}")
            return {"source": "mock", "data": {}}

    async def get_earnings(self, symbol: str) -> Dict[str, Any]:
        """获取财报数据（OpenBB可选）"""
        try:
            from openbb import obb
            data = obb.equity.fundamental.earnings(symbol=symbol)
            return {"source": "openbb", "data": data.to_dict() if hasattr(data, 'to_dict') else {}}
        except Exception as e:
            logger.debug(f"OpenBB不可用: {e}")
            return {"source": "mock", "data": {}}

    async def get_forex_rate(self, base: str = "USD", quote: str = "CNY") -> Dict[str, Any]:
        """获取汇率（OpenBB可选）"""
        try:
            from openbb import obb
            data = obb.currency.price.historical(symbol=f"{base}{quote}=X")
            return {"source": "openbb", "rate": float(data.close.iloc[-1]) if hasattr(data, 'close') else 7.25}
        except Exception as e:
            logger.debug(f"OpenBB不可用: {e}")
            return {"source": "mock", "rate": 7.25}

    # ===== Mock数据（降级兜底）=====

    def _mock_stock_data(self, symbol: str) -> Dict[str, Any]:
        mock = {
            "600519": {"name": "贵州茅台", "price": 1856.00},
            "300750": {"name": "宁德时代", "price": 218.50},
            "000858": {"name": "五粮液", "price": 156.80},
            "002594": {"name": "比亚迪", "price": 285.60},
            "601318": {"name": "中国平安", "price": 48.50},
            "600036": {"name": "招商银行", "price": 35.20},
            "AAPL": {"name": "Apple Inc.", "price": 195.50},
            "GOOGL": {"name": "Alphabet Inc.", "price": 178.20},
            "MSFT": {"name": "Microsoft Corp.", "price": 420.50},
            "TSLA": {"name": "Tesla Inc.", "price": 245.30},
        }
        data = mock.get(symbol, {"name": symbol, "price": round(np.random.uniform(10, 200), 2)})
        return {
            "symbol": symbol,
            "name": data["name"],
            "current_price": data["price"],
            "change": round(np.random.uniform(-3, 3), 2),
            "change_percent": round(np.random.uniform(-3, 3), 2),
            "volume": int(np.random.uniform(1000000, 50000000)),
            "market_cap": int(np.random.uniform(1e10, 2e12)),
            "pe_ratio": round(np.random.uniform(10, 50), 2),
            "pb_ratio": round(np.random.uniform(1, 10), 2),
            "high": round(data["price"] * 1.02, 2),
            "low": round(data["price"] * 0.98, 2),
            "open": round(data["price"] * 0.99, 2),
            "prev_close": round(data["price"] * 0.99, 2),
            "turnover_rate": round(np.random.uniform(0.5, 5), 2),
            "beta": round(np.random.uniform(0.5, 1.8), 2),
            "sector": "金融",
            "source": "mock",
        }

    def _mock_historical_data(self) -> pd.DataFrame:
        dates = pd.date_range(end=datetime.now(), periods=120, freq='D')
        np.random.seed(42)
        base = 100
        returns = np.random.normal(0.0005, 0.02, 120)
        prices = base * (1 + returns).cumprod()
        return pd.DataFrame({
            'Open': prices * (1 + np.random.uniform(-0.01, 0.01, 120)),
            'High': prices * (1 + np.random.uniform(0, 0.02, 120)),
            'Low': prices * (1 - np.random.uniform(0, 0.02, 120)),
            'Close': prices,
            'Volume': np.random.uniform(1e6, 5e7, 120).astype(int),
        }, index=dates)

    def _mock_indices(self) -> List[Dict]:
        return [
            {"name": "上证指数", "symbol": "000001", "current_price": 3200 + np.random.uniform(-50, 50), "change_percent": round(np.random.uniform(-1, 1), 2), "source": "mock"},
            {"name": "深证成指", "symbol": "399001", "current_price": 10500 + np.random.uniform(-100, 100), "change_percent": round(np.random.uniform(-1, 1), 2), "source": "mock"},
            {"name": "创业板指", "symbol": "399006", "current_price": 2100 + np.random.uniform(-50, 50), "change_percent": round(np.random.uniform(-1.5, 1.5), 2), "source": "mock"},
        ]


# 全局单例
data_adapter = DataAdapter()
