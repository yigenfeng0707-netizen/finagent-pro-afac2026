"""
BaseAgent - 所有金融智能体的基类
实现ReAct（Reasoning + Acting）推理循环
"""
import time
import json
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field

from models.schemas import AgentStep, AgentResult, SignalType

logger = logging.getLogger(__name__)


@dataclass
class Tool:
    """工具定义"""
    name: str
    description: str
    func: Callable
    parameters: Dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """
    金融智能体基类 - 实现ReAct推理循环

    核心流程:
    1. 接收任务数据
    2. Thought: 分析当前状态，决定下一步
    3. Action: 调用Tool获取数据/执行操作
    4. Observation: 观察执行结果
    5. 重复2-4直到任务完成或达到最大步数
    6. 输出最终分析结果
    """

    def __init__(
        self,
        name: str,
        agent_type: str,
        description: str = "",
        max_steps: int = 10,
    ):
        self.name = name
        self.agent_type = agent_type
        self.description = description
        self.max_steps = max_steps

        # 工具注册表
        self._tools: Dict[str, Tool] = {}

        # 运行状态
        self.is_running = False
        self.last_execution_time = None
        self.execution_count = 0
        self.error_count = 0

        # 注册通用工具
        self._register_default_tools()

    def _register_default_tools(self):
        """注册通用工具（子类可覆盖）"""
        pass

    def register_tool(self, name: str, description: str, func: Callable, parameters: Dict = None):
        """注册工具"""
        self._tools[name] = Tool(
            name=name,
            description=description,
            func=func,
            parameters=parameters or {}
        )

    def get_tool_descriptions(self) -> str:
        """获取工具描述（供LLM使用）"""
        if not self._tools:
            return "无可用工具"
        descriptions = []
        for tool in self._tools.values():
            params_str = json.dumps(tool.parameters, ensure_ascii=False) if tool.parameters else "{}"
            descriptions.append(f"- {tool.name}: {tool.description} 参数: {params_str}")
        return "\n".join(descriptions)

    async def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """执行工具调用"""
        if tool_name not in self._tools:
            return f"错误: 工具 '{tool_name}' 不存在"

        tool = self._tools[tool_name]
        try:
            result = await tool.func(**kwargs) if asyncio.iscoroutinefunction(tool.func) else tool.func(**kwargs)
            return result
        except Exception as e:
            logger.error(f"工具执行失败 [{tool_name}]: {e}")
            return f"工具执行错误: {str(e)}"

    @abstractmethod
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行分析（子类必须实现）

        Args:
            data: 输入数据
        Returns:
            分析结果字典，必须包含: signal, confidence, analysis, key_findings, risk_factors
        """
        pass

    async def react_loop(self, task_description: str, initial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        ReAct推理循环

        Args:
            task_description: 任务描述
            initial_data: 初始数据
        Returns:
            包含推理步骤和最终结果的字典
        """
        from services.llm_service import llm_service

        steps: List[AgentStep] = []
        current_context = json.dumps(initial_data, ensure_ascii=False, default=str)[:2000]
        final_answer = None

        for step_num in range(self.max_steps):
            # Thought: LLM推理下一步
            thought_prompt = f"""你是一个专业的金融分析智能体: {self.name}
{self.description}

当前任务: {task_description}

可用工具:
{self.get_tool_descriptions()}

当前已知信息:
{current_context}

已执行步骤数: {step_num}/{self.max_steps}

请分析当前状态，决定下一步行动。你必须以JSON格式回复:
{{
    "thought": "你的思考过程",
    "action": "工具名称 或 'finish'",
    "action_input": {{ 工具参数 }} 或 {{ "answer": "最终答案" }}
}}

如果已经有足够信息得出结论，action设为'finish'。"""

            try:
                llm_response = await llm_service.generate_structured(
                    system_prompt=f"你是{self.name}，{self.description}。你必须以JSON格式回复。",
                    user_prompt=thought_prompt,
                    output_schema={
                        "type": "object",
                        "properties": {
                            "thought": {"type": "string"},
                            "action": {"type": "string"},
                            "action_input": {"type": "object"}
                        }
                    }
                )
            except Exception as e:
                logger.warning(f"ReAct推理失败(step {step_num}): {e}")
                break

            thought = llm_response.get("thought", "")
            action = llm_response.get("action", "finish")
            action_input = llm_response.get("action_input", {})

            step = AgentStep(
                thought=thought,
                action=action,
                action_input=action_input,
                timestamp=datetime.now()
            )

            # 执行动作
            if action == "finish":
                final_answer = action_input.get("answer", action_input)
                step.observation = f"任务完成: {final_answer}"
                steps.append(step)
                break
            else:
                # 调用工具
                observation = await self.execute_tool(action, **action_input)
                obs_str = json.dumps(observation, ensure_ascii=False, default=str)[:1000] if not isinstance(observation, str) else observation[:1000]
                step.observation = obs_str
                steps.append(step)

                # 更新上下文
                current_context += f"\n\n[步骤{step_num + 1}] 思考: {thought}\n行动: {action}({json.dumps(action_input, ensure_ascii=False)})\n观察: {obs_str}"
                # 限制上下文长度
                if len(current_context) > 6000:
                    current_context = current_context[-4000:]

        if final_answer is None:
            final_answer = "未能通过ReAct循环得出结论，使用规则引擎兜底"

        return {
            "steps": steps,
            "final_answer": final_answer,
            "total_steps": len(steps)
        }

    async def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """执行智能体（含计时和错误处理）"""
        self.is_running = True
        start_time = time.time()

        try:
            result = await self.analyze(data)
            execution_time = time.time() - start_time
            self.last_execution_time = datetime.now()
            self.execution_count += 1

            return {
                "agent_name": self.name,
                "agent_type": self.agent_type,
                "status": "success",
                "execution_time": round(execution_time, 3),
                "timestamp": datetime.now().isoformat(),
                "result": result
            }
        except Exception as e:
            self.error_count += 1
            logger.error(f"智能体执行失败 [{self.name}]: {e}", exc_info=True)
            return {
                "agent_name": self.name,
                "agent_type": self.agent_type,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        finally:
            self.is_running = False

    async def _llm_analyze(self, system_prompt: str, user_prompt: str, output_schema: dict = None) -> dict:
        """使用LLM进行分析（便捷方法）"""
        from services.llm_service import llm_service
        if not llm_service.is_available():
            return None
        try:
            if output_schema:
                return await llm_service.generate_structured(system_prompt, user_prompt, output_schema)
            else:
                text = await llm_service.generate(system_prompt, user_prompt)
                return {"llm_analysis": text}
        except Exception as e:
            logger.warning(f"LLM分析失败 [{self.name}]: {e}")
            return None

    def get_status(self) -> Dict[str, Any]:
        """获取智能体状态"""
        return {
            "name": self.name,
            "type": self.agent_type,
            "description": self.description,
            "is_running": self.is_running,
            "last_execution": self.last_execution_time,
            "execution_count": self.execution_count,
            "error_count": self.error_count,
            "tools": list(self._tools.keys()),
            "success_rate": (
                (self.execution_count - self.error_count) / self.execution_count
                if self.execution_count > 0 else 0
            )
        }
