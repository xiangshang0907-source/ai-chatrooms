"""流式响应服务模块."""

import json
import logging
from typing import Iterator, Optional
from uuid import UUID

import requests
from flask import current_app

from ..schemas.message import AIResponseResult

logger = logging.getLogger(__name__)


class StreamingService:
    """流式AI响应服务类."""
    
    def __init__(self):
        """初始化流式服务."""
        self.api_key = current_app.config.get("QWEN_API_KEY")
        self.api_base = current_app.config.get("QWEN_API_BASE", "https://dashscope.aliyuncs.com/api/v1")
        self.model_name = "qwen-plus"
        
        if not self.api_key:
            logger.warning("QWEN_API_KEY not configured")
    
    def stream_ai_response(
        self,
        messages: list[dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> Iterator[str]:
        """
        生成流式AI响应.
        
        Args:
            messages: 对话消息列表
            system_prompt: 系统提示词
            temperature: 生成温度
            max_tokens: 最大token数
            **kwargs: 其他参数
            
        Yields:
            str: 流式响应数据
            
        Raises:
            Exception: AI服务错误
        """
        if not self.api_key:
            raise Exception("AI服务未配置API密钥")
        
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
                    "stream": True,  # 启用流式响应
                    "incremental_output": True,  # 启用增量输出
                }
            }
            
            # 发送流式请求
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "text/event-stream"
            }
            
            response = requests.post(
                f"{self.api_base}/services/aigc/text-generation/generation",
                headers=headers,
                json=request_data,
                stream=True,
                timeout=60
            )
            
            if response.status_code != 200:
                logger.error(f"AI API流式请求失败: {response.status_code} - {response.text}")
                raise Exception(f"AI API流式请求失败: {response.status_code}")
            
            # 处理流式响应
            content_buffer = ""
            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue
                
                # 解析SSE数据
                if line.startswith("data: "):
                    data_str = line[6:]  # 移除 "data: " 前缀
                    
                    if data_str.strip() == "[DONE]":
                        # 响应结束
                        break
                    
                    try:
                        data = json.loads(data_str)
                        
                        # 检查是否有输出内容
                        if "output" in data and "text" in data["output"]:
                            new_content = data["output"]["text"]
                            
                            # 如果是增量输出，计算差异
                            if new_content.startswith(content_buffer):
                                delta = new_content[len(content_buffer):]
                                content_buffer = new_content
                            else:
                                delta = new_content
                                content_buffer = new_content
                            
                            # 发送增量内容
                            if delta:
                                yield f"data: {json.dumps({'content': delta, 'type': 'content'})}\n\n"
                        
                        # 检查是否结束
                        if "output" in data and data["output"].get("finish_reason"):
                            # 发送结束信号
                            yield f"data: {json.dumps({'type': 'finish', 'finish_reason': data['output']['finish_reason']})}\n\n"
                            break
                            
                    except json.JSONDecodeError as e:
                        logger.error(f"解析流式响应JSON失败: {e}")
                        continue
            
            # 发送最终的 DONE 信号
            yield "data: [DONE]\n\n"
            
        except requests.RequestException as e:
            logger.error(f"AI API网络请求错误: {e}")
            raise Exception(f"AI服务网络错误: {str(e)}")
        except Exception as e:
            logger.error(f"AI流式服务错误: {e}")
            raise Exception(f"AI流式服务错误: {str(e)}")


def get_streaming_service() -> StreamingService:
    """获取流式服务实例."""
    return StreamingService()
