"""
统一LLM服务
支持DashScope(阿里云百炼)、GLM-5.1、DeepSeek-v4-pro、SenseNova，自动降级和重试
"""
import asyncio
import json
import logging
from typing import Optional

from config import (
    DASHSCOPE_API_KEY, DASHSCOPE_BASE_URL, DASHSCOPE_MODEL,
    GLM_API_KEY, GLM_BASE_URL, GLM_MODEL,
    DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL,
    SENSENOVA_API_KEY, SENSENOVA_BASE_URL, SENSENOVA_MODEL,
    LLM_PROVIDER, LLM_ENABLED
)

logger = logging.getLogger(__name__)


class LLMService:
    """统一LLM服务 - 四模型自动降级：DashScope → GLM-5.1 → DeepSeek → SenseNova"""

    def __init__(self):
        self.dashscope_client = None
        self.glm_client = None
        self.deepseek_client = None
        self.sensenova_client = None
        self.provider: Optional[str] = None
        self.available: bool = False
        self.default_model: Optional[str] = None

        # 所有已初始化的提供商（用于降级）
        self._providers: list = []

        # 0. Primary Model: DashScope (阿里云百炼)
        if LLM_ENABLED and DASHSCOPE_API_KEY:
            try:
                from openai import AsyncOpenAI
                self.dashscope_client = AsyncOpenAI(
                    api_key=DASHSCOPE_API_KEY,
                    base_url=DASHSCOPE_BASE_URL,
                )
                self._providers.append(("dashscope", self.dashscope_client, DASHSCOPE_MODEL))
                if not self.available:
                    self.provider = "dashscope"
                    self.default_model = DASHSCOPE_MODEL
                    self.available = True
                logger.info(f"LLM初始化: DashScope ({DASHSCOPE_MODEL}) @ {DASHSCOPE_BASE_URL}")
            except Exception as e:
                logger.warning(f"DashScope初始化失败: {e}")

        # 1. 备选模型: GLM-5.1（智谱AI）
        if LLM_ENABLED and GLM_API_KEY:
            try:
                from openai import AsyncOpenAI
                self.glm_client = AsyncOpenAI(
                    api_key=GLM_API_KEY,
                    base_url=GLM_BASE_URL,
                )
                self._providers.append(("glm", self.glm_client, GLM_MODEL))
                if not self.available:
                    self.provider = "glm"
                    self.default_model = GLM_MODEL
                    self.available = True
                logger.info(f"LLM初始化: GLM-5.1 ({GLM_MODEL}) @ {GLM_BASE_URL}")
            except Exception as e:
                logger.warning(f"GLM-5.1初始化失败: {e}")

        # 2. 备选模型: DeepSeek-v4-pro
        if LLM_ENABLED and DEEPSEEK_API_KEY:
            try:
                from openai import AsyncOpenAI
                self.deepseek_client = AsyncOpenAI(
                    api_key=DEEPSEEK_API_KEY,
                    base_url=DEEPSEEK_BASE_URL,
                )
                self._providers.append(("deepseek", self.deepseek_client, DEEPSEEK_MODEL))
                if not self.available:
                    self.provider = "deepseek"
                    self.default_model = DEEPSEEK_MODEL
                    self.available = True
                logger.info(f"LLM初始化: DeepSeek ({DEEPSEEK_MODEL}) @ {DEEPSEEK_BASE_URL}")
            except Exception as e:
                logger.warning(f"DeepSeek初始化失败: {e}")

        # 3. 轻量模型: SenseNova
        if LLM_ENABLED and SENSENOVA_API_KEY:
            try:
                from openai import AsyncOpenAI
                self.sensenova_client = AsyncOpenAI(
                    api_key=SENSENOVA_API_KEY,
                    base_url=SENSENOVA_BASE_URL,
                )
                self._providers.append(("sensenova", self.sensenova_client, SENSENOVA_MODEL))
                if not self.available:
                    self.provider = "sensenova"
                    self.default_model = SENSENOVA_MODEL
                    self.available = True
                logger.info(f"LLM初始化: SenseNova ({SENSENOVA_MODEL}) @ {SENSENOVA_BASE_URL}")
            except Exception as e:
                logger.warning(f"SenseNova初始化失败: {e}")

        if not self.available:
            logger.warning("无可用LLM提供商，将使用规则引擎模式")
        else:
            logger.info(f"已初始化 {len(self._providers)} 个LLM提供商，主提供商: {self.provider}")

    def is_available(self) -> bool:
        return self.available

    async def _retry_request(self, func, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 10.0):
        """指数退避重试"""
        last_exception = None
        for attempt in range(max_retries):
            try:
                return await func()
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    logger.warning(f"LLM请求失败({attempt + 1}/{max_retries})，{delay:.1f}s后重试: {e}")
                    await asyncio.sleep(delay)
        raise last_exception

    async def generate(self, system_prompt: str, user_prompt: str, model: str = None,
                       temperature: float = 0.3, max_tokens: int = 4096) -> str:
        """生成文本补全"""
        if not self.available:
            return ""

        # 使用主提供商
        try:
            for provider_name, client, default_model in self._providers:
                if provider_name == self.provider:
                    return await self._retry_request(
                        lambda c=client, m=model or default_model: self._generate_openai_compat(
                            c, m, system_prompt, user_prompt, temperature, max_tokens
                        )
                    )
        except Exception as e:
            logger.error(f"LLM生成失败({self.provider}): {e}")
            # 尝试降级到其他提供商
            fallback = await self._try_fallback(system_prompt, user_prompt, model, temperature, max_tokens)
            if fallback is not None:
                return fallback
        return ""

    async def _generate_openai_compat(self, client, model: str, system_prompt: str,
                                       user_prompt: str, temperature: float, max_tokens: int) -> str:
        """OpenAI兼容接口生成（GLM/DeepSeek/SenseNova均兼容）"""
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if response.choices and len(response.choices) > 0 and response.choices[0].message:
            return response.choices[0].message.content or ""
        return ""

    async def _try_fallback(self, system_prompt: str, user_prompt: str, model: str,
                            temperature: float, max_tokens: int) -> Optional[str]:
        """降级到其他LLM提供商"""
        for provider_name, client, fallback_model in self._providers:
            if provider_name == self.provider:
                continue  # 跳过已失败的主提供商
            try:
                logger.info(f"降级到 {provider_name} ({fallback_model})")
                return await self._generate_openai_compat(
                    client, fallback_model, system_prompt, user_prompt, temperature, max_tokens
                )
            except Exception as e:
                logger.error(f"{provider_name} 降级失败: {e}")
        return None

    async def generate_structured(self, system_prompt: str, user_prompt: str,
                                   output_schema: dict, model: str = None) -> dict:
        """生成结构化JSON输出"""
        if not self.available:
            return self._default_structure(output_schema)

        schema_str = json.dumps(output_schema, indent=2, ensure_ascii=False)
        structured_instruction = (
            f"{system_prompt}\n\n"
            "你必须以合法的JSON格式回复，符合以下Schema。不要在JSON之外添加任何文字。\n\n"
            f"Schema:\n{schema_str}"
        )

        try:
            raw = await self.generate(
                system_prompt=structured_instruction,
                user_prompt=user_prompt,
                model=model,
                temperature=0.2,
                max_tokens=4096,
            )

            # 清理markdown代码块
            text = raw.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                lines = [l for l in lines if not l.strip().startswith("```")]
                text = "\n".join(lines).strip()

            result = json.loads(text)
            return result
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            return self._default_structure(output_schema)
        except Exception as e:
            logger.error(f"结构化生成失败: {e}")
            return self._default_structure(output_schema)

    @staticmethod
    def _default_structure(schema: dict) -> dict:
        """从Schema构建默认空结构"""
        result = {}
        properties = schema.get("properties", {})
        for key, prop in properties.items():
            prop_type = prop.get("type", "string")
            if prop_type == "string":
                result[key] = ""
            elif prop_type == "number":
                result[key] = 0.0
            elif prop_type == "integer":
                result[key] = 0
            elif prop_type == "boolean":
                result[key] = False
            elif prop_type == "array":
                result[key] = []
            elif prop_type == "object":
                result[key] = {}
            else:
                result[key] = None
        return result

    @staticmethod
    def validate_agent_result(result: dict) -> dict:
        """验证和修正智能体LLM输出"""
        valid_signals = {"strong_buy", "buy", "hold", "sell", "strong_sell"}

        if "signal" in result:
            signal = result["signal"]
            if signal not in valid_signals:
                signal_map = {
                    "strong buy": "strong_buy", "强烈买入": "strong_buy",
                    "buy": "buy", "买入": "buy",
                    "hold": "hold", "持有": "hold", "中性": "hold",
                    "sell": "sell", "卖出": "sell",
                    "strong sell": "strong_sell", "强烈卖出": "strong_sell",
                }
                result["signal"] = signal_map.get(signal, "hold")

        if "confidence" in result:
            try:
                conf = float(result["confidence"])
                result["confidence"] = round(max(0, min(1, conf)), 2)
            except (ValueError, TypeError):
                result["confidence"] = 0.5

        for key in ["key_findings", "risk_factors", "risk_warnings"]:
            if key in result:
                if not isinstance(result[key], list):
                    result[key] = []
                else:
                    result[key] = [str(f) for f in result[key] if f is not None]

        return result


# 单例
llm_service = LLMService()
