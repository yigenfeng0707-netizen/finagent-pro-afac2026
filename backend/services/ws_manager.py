"""
WebSocket连接管理器
用于实时推送智能体进度、预警通知等
"""
import json
import logging
from typing import Dict, List, Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """WebSocket连接管理器"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """接受WebSocket连接"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket连接建立，当前连接数: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """断开WebSocket连接"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket连接断开，当前连接数: {len(self.active_connections)}")

    async def send_personal(self, websocket: WebSocket, message: Dict):
        """发送个人消息"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.warning(f"发送WebSocket消息失败: {e}")

    async def broadcast(self, message: Dict):
        """广播消息"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)

    async def send_agent_progress(self, symbol: str, agent_name: str, status: str, data: Any = None):
        """推送智能体执行进度"""
        await self.broadcast({
            "type": "agent_progress",
            "symbol": symbol,
            "agent_name": agent_name,
            "status": status,
            "data": data,
        })

    async def send_analysis_complete(self, symbol: str, result: Dict):
        """推送分析完成"""
        await self.broadcast({
            "type": "analysis_complete",
            "symbol": symbol,
            "result": result,
        })

    async def send_alert(self, alert: Dict):
        """推送预警通知"""
        await self.broadcast({
            "type": "alert",
            "alert": alert,
        })

    async def send_thinking_step(self, symbol: str, agent_name: str, step: Dict):
        """推送思维链步骤（实时可视化）"""
        await self.broadcast({
            "type": "thinking_step",
            "symbol": symbol,
            "agent_name": agent_name,
            "step": step,
        })

    async def handle_message(self, websocket: WebSocket, data: str):
        """处理客户端消息"""
        try:
            message = json.loads(data)
            msg_type = message.get("type", "")
            if msg_type == "ping":
                await self.send_personal(websocket, {"type": "pong"})
            elif msg_type == "subscribe":
                # 订阅特定股票的实时更新
                await self.send_personal(websocket, {"type": "subscribed", "symbols": message.get("symbols", [])})
        except json.JSONDecodeError:
            logger.warning(f"无效的WebSocket消息: {data[:100]}")


# 单例
ws_manager = WebSocketManager()
