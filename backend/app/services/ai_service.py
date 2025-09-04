"""AI服务集成模块."""

import json
import logging

import requests
from flask import current_app

from ..schemas.message import AIResponseResult

logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """AI服务错误基类."""
    pass


class AIService:
    """AI服务集成类."""

    def __init__(self):
        """初始化AI服务."""
        self.api_key = current_app.config.get("QWEN_API_KEY")
        self.api_base = current_app.config.get("QWEN_API_BASE", "https://dashscope.aliyuncs.com/api/v1")
        self.model_name = "qwen-plus"  # 默认模型

        if not self.api_key:
            logger.warning("QWEN_API_KEY not configured")

    def generate_response(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> AIResponseResult:
        """
        生成AI响应.
        
        Args:
            messages: 对话消息列表 [{"role": "user", "content": "..."}, ...]
            system_prompt: 系统提示词
            temperature: 生成温度
            max_tokens: 最大token数
            **kwargs: 其他参数
            
        Returns:
            AIResponseResult: AI响应结果
            
        Raises:
            AIServiceError: AI服务错误
        """
        if not self.api_key:
            raise AIServiceError("AI服务未配置API密钥")

        try:
            # 构建请求消息
            api_messages = []

            # 添加系统提示词
            if system_prompt:
                api_messages.append({
                    "role": "system",
                    "content": system_prompt
                })

            # 添加对话消息
            api_messages.extend(messages)

            # 构建请求数据
            request_data = {
                "model": self.model_name,
                "messages": api_messages,
                "parameters": {
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "top_p": kwargs.get("top_p", 0.8),
                    "repetition_penalty": kwargs.get("repetition_penalty", 1.1),
                }
            }

            # 发送请求
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

            response = requests.post(
                f"{self.api_base}/services/aigc/text-generation/generation",
                headers=headers,
                json=request_data,
                timeout=30
            )

            if response.status_code != 200:
                logger.error(f"AI API请求失败: {response.status_code} - {response.text}")
                raise AIServiceError(f"AI API请求失败: {response.status_code}")

            result = response.json()

            # 检查响应格式
            if "output" not in result:
                logger.error(f"AI API响应格式错误: {result}")
                raise AIServiceError("AI API响应格式错误")

            output = result["output"]
            usage = result.get("usage", {})

            # 提取响应内容
            content = output.get("text", "")
            if not content:
                logger.error(f"AI API返回空内容: {result}")
                raise AIServiceError("AI API返回空内容")

            return AIResponseResult(
                content=content,
                usage_tokens=usage.get("total_tokens"),
                model_name=self.model_name,
                finish_reason=output.get("finish_reason"),
                extra_info={
                    "usage": usage,
                    "request_id": result.get("request_id")
                }
            )

        except requests.RequestException as e:
            logger.error(f"AI API网络请求错误: {e}")
            raise AIServiceError(f"AI服务网络错误: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"AI API响应JSON解析错误: {e}")
            raise AIServiceError(f"AI服务响应解析错误: {str(e)}")
        except Exception as e:
            logger.error(f"AI服务未知错误: {e}")
            raise AIServiceError(f"AI服务错误: {str(e)}")

    def build_conversation_context(
        self,
        messages: list,
        max_context_length: int = 10
    ) -> list[dict[str, str]]:
        """
        构建对话上下文.
        
        Args:
            messages: 消息列表
            max_context_length: 最大上下文长度
            
        Returns:
            list[dict[str, str]]: 对话上下文
        """
        context = []

        # 只取最近的消息作为上下文
        recent_messages = messages[-max_context_length:] if len(messages) > max_context_length else messages

        for msg in recent_messages:
            # 根据参与者类型确定角色
            if hasattr(msg, 'participant') and msg.participant:
                if msg.participant.type.value == "human":
                    role = "user"
                elif msg.participant.type.value == "agent":
                    role = "assistant"
                else:
                    continue  # 跳过其他类型
            else:
                continue

            context.append({
                "role": role,
                "content": msg.content
            })

        return context


def get_ai_service() -> AIService:
    """获取AI服务实例."""
    return AIService()

