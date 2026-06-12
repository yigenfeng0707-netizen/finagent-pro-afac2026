"""
智能体记忆系统
支持三种记忆类型：工作记忆、情节记忆、语义记忆
"""
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class WorkingMemory:
    """工作记忆 - 当前对话/任务的临时上下文"""

    def __init__(self, max_items: int = 50):
        self.max_items = max_items
        self.items: List[Dict[str, Any]] = []

    def add(self, key: str, value: Any, metadata: Dict = None):
        """添加工作记忆项"""
        item = {
            "key": key,
            "value": value,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }
        self.items.append(item)
        # 超出容量时移除最早的
        if len(self.items) > self.max_items:
            self.items = self.items[-self.max_items:]

    def get(self, key: str) -> Optional[Any]:
        """获取工作记忆项"""
        for item in reversed(self.items):
            if item["key"] == key:
                return item["value"]
        return None

    def get_recent(self, n: int = 5) -> List[Dict]:
        """获取最近n条工作记忆"""
        return self.items[-n:]

    def clear(self):
        """清空工作记忆"""
        self.items = []

    def to_context_string(self, max_length: int = 2000) -> str:
        """转换为上下文字符串（供LLM使用）"""
        context_parts = []
        current_length = 0
        for item in reversed(self.items):
            part = f"[{item['key']}]: {json.dumps(item['value'], ensure_ascii=False, default=str)[:200]}"
            if current_length + len(part) > max_length:
                break
            context_parts.insert(0, part)
            current_length += len(part)
        return "\n".join(context_parts)


class EpisodicMemory:
    """情节记忆 - 历史任务执行记录"""

    def __init__(self, max_episodes: int = 100):
        self.max_episodes = max_episodes
        self.episodes: List[Dict[str, Any]] = []

    def add_episode(
        self,
        task_type: str,
        task_description: str,
        result: Dict[str, Any],
        success: bool = True
    ):
        """记录一次任务执行"""
        episode = {
            "task_type": task_type,
            "task_description": task_description,
            "result_summary": json.dumps(result, ensure_ascii=False, default=str)[:500],
            "success": success,
            "timestamp": datetime.now().isoformat()
        }
        self.episodes.append(episode)
        if len(self.episodes) > self.max_episodes:
            self.episodes = self.episodes[-self.max_episodes:]

    def get_similar_episodes(self, task_type: str, limit: int = 3) -> List[Dict]:
        """获取相似类型的历史任务"""
        similar = [e for e in self.episodes if e["task_type"] == task_type]
        return similar[-limit:]

    def get_recent_episodes(self, limit: int = 10) -> List[Dict]:
        """获取最近的任务记录"""
        return self.episodes[-limit:]


class SemanticMemory:
    """语义记忆 - 金融知识库"""

    def __init__(self):
        self.knowledge: Dict[str, Any] = {}
        self._init_default_knowledge()

    def _init_default_knowledge(self):
        """初始化默认金融知识"""
        self.knowledge = {
            "技术指标": {
                "RSI": "相对强弱指标，>70超买，<30超卖",
                "MACD": "指数平滑异同移动平均线，金叉看多，死叉看空",
                "KDJ": "随机指标，K线上穿D线为买入信号",
                "布林带": "价格触及上轨超买，触及下轨超卖",
                "ATR": "真实波动幅度，衡量市场波动性"
            },
            "风险指标": {
                "VaR": "风险价值，在给定置信水平下的最大可能损失",
                "Beta": "贝塔系数，衡量个股相对大盘的波动性",
                "夏普比率": "风险调整后收益，>1为良好"
            },
            "合规规则": {
                "单股集中度": "单一标的不超过组合10%",
                "行业集中度": "单一行业不超过组合30%",
                "创业板限制": "创业板标的合计不超过20%",
                "ST股限制": "禁止买入ST/*ST股"
            },
            "行业分类": {
                "白酒": ["600519", "000858", "000568"],
                "银行": ["601398", "600036", "601166"],
                "新能源": ["300750", "002594", "601012"],
                "半导体": ["688981", "002049", "688012"]
            }
        }

    def get(self, category: str, key: str = None) -> Any:
        """获取知识"""
        if key:
            return self.knowledge.get(category, {}).get(key)
        return self.knowledge.get(category)

    def add(self, category: str, key: str, value: Any):
        """添加知识"""
        if category not in self.knowledge:
            self.knowledge[category] = {}
        self.knowledge[category][key] = value

    def search(self, query: str) -> List[Dict]:
        """搜索相关知识"""
        results = []
        query_lower = query.lower()
        for category, items in self.knowledge.items():
            if isinstance(items, dict):
                for key, value in items.items():
                    if query_lower in key.lower() or query_lower in str(value).lower():
                        results.append({"category": category, "key": key, "value": value})
            elif isinstance(items, list):
                if query_lower in category.lower():
                    results.append({"category": category, "items": items})
        return results[:10]


class AgentMemory:
    """智能体记忆系统 - 整合三种记忆"""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.working = WorkingMemory()
        self.episodic = EpisodicMemory()
        self.semantic = SemanticMemory()

    def add_working(self, key: str, value: Any, metadata: Dict = None):
        """添加工作记忆"""
        self.working.add(key, value, metadata)

    def get_working(self, key: str) -> Optional[Any]:
        """获取工作记忆"""
        return self.working.get(key)

    def record_episode(self, task_type: str, description: str, result: Dict, success: bool = True):
        """记录情节记忆"""
        self.episodic.add_episode(task_type, description, result, success)

    def get_similar_experience(self, task_type: str) -> List[Dict]:
        """获取相似经验"""
        return self.episodic.get_similar_episodes(task_type)

    def query_knowledge(self, query: str) -> List[Dict]:
        """查询语义记忆"""
        return self.semantic.search(query)

    def get_context_for_llm(self, max_length: int = 2000) -> str:
        """获取供LLM使用的上下文"""
        parts = []

        # 工作记忆
        working_ctx = self.working.to_context_string(max_length // 2)
        if working_ctx:
            parts.append(f"【当前上下文】\n{working_ctx}")

        # 最近经验
        recent = self.episodic.get_recent_episodes(3)
        if recent:
            exp_str = "\n".join(
                f"- {e['task_type']}: {e['task_description'][:50]} ({'成功' if e['success'] else '失败'})"
                for e in recent
            )
            parts.append(f"【最近经验】\n{exp_str}")

        return "\n\n".join(parts)

    def clear_working(self):
        """清空工作记忆"""
        self.working.clear()


# 全局记忆管理器
_memory_instances: Dict[str, AgentMemory] = {}


def get_agent_memory(agent_name: str) -> AgentMemory:
    """获取智能体记忆实例（单例）"""
    if agent_name not in _memory_instances:
        _memory_instances[agent_name] = AgentMemory(agent_name)
    return _memory_instances[agent_name]
