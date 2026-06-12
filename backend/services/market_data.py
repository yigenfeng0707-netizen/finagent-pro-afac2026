"""
中国市场数据服务
基于AKShare获取A股/基金/期货数据
"""
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# 尝试导入akshare
try:
    import akshare as ak
    AK_AVAILABLE = True
except ImportError:
    AK_AVAILABLE = False
    logger.warning("akshare未安装，将使用模拟数据")

try:
    from ta.trend import SMAIndicator, MACD
    from ta.momentum import RSIIndicator
    from ta.volatility import BollingerBands, AverageTrueRange
    TA_AVAILABLE = True
except ImportError:
    TA_AVAILABLE = False


class MarketDataService:
    """A股市场数据服务"""

    def __init__(self):
        self.cache = {}
        self.cache_ts = {}
        self.cache_ttl = 300  # 5分钟缓存

    def _get_cached(self, key: str) -> Optional[Any]:
        if key in self.cache and key in self.cache_ts:
            if time.time() - self.cache_ts[key] < self.cache_ttl:
                return self.cache[key]
        return None

    def _set_cache(self, key: str, value: Any):
        self.cache[key] = value
        self.cache_ts[key] = time.time()

    async def get_stock_data(self, symbol: str) -> Dict[str, Any]:
        """获取A股实时行情"""
        cache_key = f"stock_{symbol}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        if not AK_AVAILABLE:
            return self._mock_stock_data(symbol)

        try:
            # AKShare获取实时行情
            df = ak.stock_zh_a_spot_em()
            row = df[df['代码'] == symbol]
            if row.empty:
                return self._mock_stock_data(symbol)

            r = row.iloc[0]
            result = {
                "symbol": symbol,
                "name": str(r.get('名称', symbol)),
                "current_price": float(r.get('最新价', 0)),
                "change": float(r.get('涨跌额', 0)),
                "change_percent": float(r.get('涨跌幅', 0)),
                "volume": int(r.get('成交量', 0)) if pd.notna(r.get('成交量')) else 0,
                "amount": float(r.get('成交额', 0)) if pd.notna(r.get('成交额')) else 0,
                "high": float(r.get('最高', 0)),
                "low": float(r.get('最低', 0)),
                "open": float(r.get('今开', 0)),
                "prev_close": float(r.get('昨收', 0)),
                "market_cap": float(r.get('总市值', 0)) if pd.notna(r.get('总市值')) else None,
                "pe_ratio": float(r.get('市盈率-动态', 0)) if pd.notna(r.get('市盈率-动态')) else None,
                "pb_ratio": float(r.get('市净率', 0)) if pd.notna(r.get('市净率')) else None,
                "turnover_rate": float(r.get('换手率', 0)) if pd.notna(r.get('换手率')) else None,
            }
            self._set_cache(cache_key, result)
            return result
        except Exception as e:
            logger.warning(f"AKShare获取行情失败: {e}，使用模拟数据")
            return self._mock_stock_data(symbol)

    async def get_historical_data(self, symbol: str, period: str = "6mo", interval: str = "daily") -> pd.DataFrame:
        """获取历史K线数据"""
        if not AK_AVAILABLE:
            return self._mock_historical_data()

        try:
            period_map = {"1mo": "30", "3mo": "90", "6mo": "180", "1y": "365"}
            ak_period = period_map.get(period, "180")
            df = ak.stock_zh_a_hist(symbol=symbol, period=interval, start_date="", end_date="", adjust="qfq")
            if df.empty:
                return self._mock_historical_data()
            # 取最近N天
            df = df.tail(int(ak_period))
            df = df.rename(columns={"日期": "Date", "开盘": "Open", "收盘": "Close", "最高": "High", "最低": "Low", "成交量": "Volume"})
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.set_index('Date')
            for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            return df
        except Exception as e:
            logger.warning(f"获取历史数据失败: {e}")
            return self._mock_historical_data()

    async def calculate_technical_indicators(self, symbol: str) -> Dict[str, Any]:
        """计算技术指标"""
        if not TA_AVAILABLE:
            return self._mock_indicators()

        try:
            df = await self.get_historical_data(symbol, period="6mo")
            if df.empty or len(df) < 50:
                return self._mock_indicators()

            close = df['Close']
            high = df['High']
            low = df['Low']

            indicators = {"current_price": round(float(close.iloc[-1]), 2)}

            # SMA
            sma_20 = SMAIndicator(close=close, window=20).sma_indicator()
            sma_50 = SMAIndicator(close=close, window=50).sma_indicator()
            indicators["sma_20"] = round(float(sma_20.iloc[-1]), 2) if not pd.isna(sma_20.iloc[-1]) else None
            indicators["sma_50"] = round(float(sma_50.iloc[-1]), 2) if not pd.isna(sma_50.iloc[-1]) else None

            # RSI
            rsi = RSIIndicator(close=close, window=14).rsi()
            indicators["rsi_14"] = round(float(rsi.iloc[-1]), 2) if not pd.isna(rsi.iloc[-1]) else None

            # MACD
            macd_obj = MACD(close=close)
            indicators["macd"] = round(float(macd_obj.macd().iloc[-1]), 4) if not pd.isna(macd_obj.macd().iloc[-1]) else None
            indicators["macd_signal"] = round(float(macd_obj.macd_signal().iloc[-1]), 4) if not pd.isna(macd_obj.macd_signal().iloc[-1]) else None

            # Bollinger
            bb = BollingerBands(close=close, window=20)
            indicators["bollinger_upper"] = round(float(bb.bollinger_hband().iloc[-1]), 2) if not pd.isna(bb.bollinger_hband().iloc[-1]) else None
            indicators["bollinger_lower"] = round(float(bb.bollinger_lband().iloc[-1]), 2) if not pd.isna(bb.bollinger_lband().iloc[-1]) else None

            # ATR
            atr = AverageTrueRange(high=high, low=low, close=close, window=14)
            indicators["atr_14"] = round(float(atr.average_true_range().iloc[-1]), 2) if not pd.isna(atr.average_true_range().iloc[-1]) else None

            return indicators
        except Exception as e:
            logger.warning(f"计算技术指标失败: {e}")
            return self._mock_indicators()

    async def get_market_overview(self) -> Dict[str, Any]:
        """获取A股市场概览"""
        if not AK_AVAILABLE:
            return {"indices": self._mock_indices(), "timestamp": datetime.now().isoformat()}

        try:
            df = ak.stock_zh_index_spot_em()
            indices_map = {"000001": "上证指数", "399001": "深证成指", "399006": "创业板指"}
            indices = []
            for code, name in indices_map.items():
                row = df[df['代码'] == code]
                if not row.empty:
                    r = row.iloc[0]
                    indices.append({"name": name, "symbol": code, "current_price": float(r.get('最新价', 0)), "change_percent": float(r.get('涨跌幅', 0))})
            return {"indices": indices, "timestamp": datetime.now().isoformat()}
        except:
            return {"indices": self._mock_indices(), "timestamp": datetime.now().isoformat()}

    async def get_financial_data(self, symbol: str) -> Dict[str, Any]:
        """获取财务数据"""
        stock = await self.get_stock_data(symbol)
        return stock  # AKShare实时行情已含PE/PB

    async def get_capital_flow(self, symbol: str) -> Dict[str, Any]:
        """获取资金流向"""
        if not AK_AVAILABLE:
            return {"main_net_inflow": 0, "retail_net_inflow": 0}
        try:
            df = ak.stock_individual_fund_flow(stock=symbol, market="sh" if symbol.startswith("6") else "sz")
            if df.empty:
                return {"main_net_inflow": 0, "retail_net_inflow": 0}
            latest = df.iloc[-1]
            return {"main_net_inflow": float(latest.get('主力净流入-净额', 0)), "retail_net_inflow": float(latest.get('散户净流入-净额', 0))}
        except:
            return {"main_net_inflow": 0, "retail_net_inflow": 0}

    async def get_sector_comparison(self, sector: str, metric: str = "pe") -> Dict[str, Any]:
        """获取行业对比"""
        return {"sector": sector, "metric": metric, "data": "行业对比数据暂不可用"}

    async def get_dragon_tiger(self, symbol: str = None, date: str = None) -> Dict[str, Any]:
        """获取龙虎榜"""
        return {"data": "龙虎榜数据暂不可用"}

    async def get_chart_data(self, symbol: str, period: str = "6mo") -> Dict[str, Any]:
        """获取K线图数据"""
        try:
            df = await self.get_historical_data(symbol, period)
            if df.empty:
                return {"status": "error", "error": "无历史数据"}

            candles = []
            for i in range(len(df)):
                ts = int(df.index[i].timestamp()) if hasattr(df.index[i], 'timestamp') else int(datetime.now().timestamp())
                candles.append({"time": ts, "open": round(float(df['Open'].iloc[i]), 2), "high": round(float(df['High'].iloc[i]), 2), "low": round(float(df['Low'].iloc[i]), 2), "close": round(float(df['Close'].iloc[i]), 2)})

            return {"status": "success", "symbol": symbol, "candles": candles}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # ===== 模拟数据 =====

    def _mock_stock_data(self, symbol: str) -> Dict[str, Any]:
        mock = {"600519": {"name": "贵州茅台", "price": 1856.00}, "300750": {"name": "宁德时代", "price": 218.50}, "000858": {"name": "五粮液", "price": 156.80}, "002594": {"name": "比亚迪", "price": 285.60}, "601318": {"name": "中国平安", "price": 48.50}, "600036": {"name": "招商银行", "price": 35.20}}
        data = mock.get(symbol, {"name": f"{symbol}", "price": round(np.random.uniform(10, 200), 2)})
        return {"symbol": symbol, "name": data["name"], "current_price": data["price"], "change": round(np.random.uniform(-3, 3), 2), "change_percent": round(np.random.uniform(-3, 3), 2), "volume": int(np.random.uniform(1000000, 50000000)), "market_cap": int(np.random.uniform(1e10, 2e12)), "pe_ratio": round(np.random.uniform(10, 50), 2), "pb_ratio": round(np.random.uniform(1, 10), 2), "high_52w": round(data["price"] * 1.3, 2), "low_52w": round(data["price"] * 0.7, 2), "beta": round(np.random.uniform(0.5, 1.8), 2), "sector": "金融", "turnover_rate": round(np.random.uniform(0.5, 5), 2)}

    def _mock_historical_data(self) -> pd.DataFrame:
        dates = pd.date_range(end=datetime.now(), periods=120, freq='D')
        np.random.seed(42)
        base = 100
        returns = np.random.normal(0.0005, 0.02, 120)
        prices = base * (1 + returns).cumprod()
        return pd.DataFrame({'Open': prices * (1 + np.random.uniform(-0.01, 0.01, 120)), 'High': prices * (1 + np.random.uniform(0, 0.02, 120)), 'Low': prices * (1 - np.random.uniform(0, 0.02, 120)), 'Close': prices, 'Volume': np.random.uniform(1e6, 5e7, 120).astype(int)}, index=dates)

    def _mock_indicators(self) -> Dict[str, Any]:
        price = 100.0
        return {"sma_20": round(price * 0.98, 2), "sma_50": round(price * 0.95, 2), "rsi_14": round(np.random.uniform(35, 65), 2), "macd": round(np.random.uniform(-1, 1), 4), "macd_signal": round(np.random.uniform(-1, 1), 4), "bollinger_upper": round(price * 1.05, 2), "bollinger_lower": round(price * 0.95, 2), "atr_14": round(price * 0.02, 2), "current_price": price}

    def _mock_indices(self) -> List[Dict]:
        return [{"name": "上证指数", "symbol": "000001", "current_price": 3200 + np.random.uniform(-50, 50), "change_percent": round(np.random.uniform(-1, 1), 2)}, {"name": "深证成指", "symbol": "399001", "current_price": 10500 + np.random.uniform(-100, 100), "change_percent": round(np.random.uniform(-1, 1), 2)}, {"name": "创业板指", "symbol": "399006", "current_price": 2100 + np.random.uniform(-50, 50), "change_percent": round(np.random.uniform(-1.5, 1.5), 2)}]


# 单例
market_data_service = MarketDataService()
