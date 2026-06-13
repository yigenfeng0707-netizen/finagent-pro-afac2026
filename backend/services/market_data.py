"""
中国市场数据服务
基于统一数据适配层获取A股/海外市场数据
自动降级：真实数据 → 缓存 → Mock数据
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

import pandas as pd
import numpy as np

from services.data_adapter import data_adapter

logger = logging.getLogger(__name__)

try:
    from ta.trend import SMAIndicator, MACD
    from ta.momentum import RSIIndicator
    from ta.volatility import BollingerBands, AverageTrueRange
    TA_AVAILABLE = True
except ImportError:
    TA_AVAILABLE = False


class MarketDataService:
    """A股市场数据服务（委托给data_adapter）"""

    async def get_stock_data(self, symbol: str) -> Dict[str, Any]:
        """获取股票实时行情"""
        return await data_adapter.get_stock_quote(symbol)

    async def get_historical_data(self, symbol: str, period: str = "6mo", interval: str = "daily") -> pd.DataFrame:
        """获取历史K线数据"""
        return await data_adapter.get_historical_data(symbol, period)

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
        """获取市场概览"""
        return await data_adapter.get_market_overview()

    async def get_financial_data(self, symbol: str) -> Dict[str, Any]:
        """获取财务数据"""
        return await data_adapter.get_financial_data(symbol)

    async def get_capital_flow(self, symbol: str) -> Dict[str, Any]:
        """获取资金流向"""
        return await data_adapter.get_capital_flow(symbol)

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

    # ===== 模拟数据（技术指标降级）=====

    def _mock_indicators(self) -> Dict[str, Any]:
        price = 100.0
        return {"sma_20": round(price * 0.98, 2), "sma_50": round(price * 0.95, 2), "rsi_14": round(np.random.uniform(35, 65), 2), "macd": round(np.random.uniform(-1, 1), 4), "macd_signal": round(np.random.uniform(-1, 1), 4), "bollinger_upper": round(price * 1.05, 2), "bollinger_lower": round(price * 0.95, 2), "atr_14": round(price * 0.02, 2), "current_price": price}


# 单例
market_data_service = MarketDataService()
