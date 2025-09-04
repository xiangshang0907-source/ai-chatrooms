"""消息相关的数据模式定义."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from ..models.message import MessageStatus, MessageType
from ..models.participant import ParticipantType


class MessageSendRequest(BaseModel):
    """发送消息请求."""

    content: str = Field(..., min_length=1, max_length=10000, description="消息内容")
    reply_to_id: UUID | None = Field(None, description="回复的消息ID")
    extra_data: dict[str, Any] | None = Field(None, description="扩展数据")


class ParticipantInfo(BaseModel):
    """参与者信息."""

    id: UUID
    type: ParticipantType
    display_name: str
    user_id: UUID | None
    agent_profile_id: UUID | None

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """消息响应."""

    id: UUID
    content: str
    type: MessageType
    status: MessageStatus
    sequence_number: int
    reply_to_id: UUID | None
    extra_data: dict[str, Any] | None
    room_id: UUID
    participant_id: UUID
    run_id: UUID | None
    created_at: datetime
    updated_at: datetime

    # 关联信息
    participant: ParticipantInfo | None = None

    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    """消息列表响应."""

    messages: list[MessageResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool


class AIResponseRequest(BaseModel):
    """AI响应请求（内部使用）."""

    room_id: UUID
    user_message_id: UUID
    conversation_context: list[dict[str, str]]
    agent_profile_id: UUID | None = None


class AIResponseResult(BaseModel):
    """AI响应结果."""

    content: str
    usage_tokens: int | None = None
    model_name: str | None = None
    finish_reason: str | None = None
    extra_info: dict[str, Any] | None = None


class ConversationStartRequest(BaseModel):
    """开始对话请求."""

    name: str | None = Field(None, max_length=200, description="对话名称")
    description: str | None = Field(None, max_length=500, description="对话描述")
    config: dict[str, Any] | None = Field(None, description="对话配置")


class ConversationResponse(BaseModel):
    """对话响应."""

    id: UUID
    name: str | None
    description: str | None
    status: str  # RunStatus enum value
    total_rounds: int
    total_tokens_used: int | None
    estimated_cost: float | None
    started_at: datetime
    ended_at: datetime | None
    config_snapshot: dict[str, Any] | None
    room_id: UUID
    started_by_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

