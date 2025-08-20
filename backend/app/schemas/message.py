"""消息相关的数据模式定义."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from ..models.message import MessageStatus, MessageType
from ..models.participant import ParticipantType


class MessageSendRequest(BaseModel):
    """发送消息请求."""
    
    content: str = Field(..., min_length=1, max_length=10000, description="消息内容")
    reply_to_id: Optional[UUID] = Field(None, description="回复的消息ID")
    extra_data: Optional[dict[str, Any]] = Field(None, description="扩展数据")


class ParticipantInfo(BaseModel):
    """参与者信息."""
    
    id: UUID
    type: ParticipantType
    display_name: str
    user_id: Optional[UUID]
    agent_profile_id: Optional[UUID]

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """消息响应."""
    
    id: UUID
    content: str
    type: MessageType
    status: MessageStatus
    sequence_number: int
    reply_to_id: Optional[UUID]
    extra_data: Optional[dict[str, Any]]
    room_id: UUID
    participant_id: UUID
    run_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    
    # 关联信息
    participant: Optional[ParticipantInfo] = None

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
    agent_profile_id: Optional[UUID] = None


class AIResponseResult(BaseModel):
    """AI响应结果."""
    
    content: str
    usage_tokens: Optional[int] = None
    model_name: Optional[str] = None
    finish_reason: Optional[str] = None
    extra_info: Optional[dict[str, Any]] = None


class ConversationStartRequest(BaseModel):
    """开始对话请求."""
    
    name: Optional[str] = Field(None, max_length=200, description="对话名称")
    description: Optional[str] = Field(None, max_length=500, description="对话描述")
    config: Optional[dict[str, Any]] = Field(None, description="对话配置")


class ConversationResponse(BaseModel):
    """对话响应."""
    
    id: UUID
    name: Optional[str]
    description: Optional[str]
    status: str  # RunStatus enum value
    total_rounds: int
    total_tokens_used: Optional[int]
    estimated_cost: Optional[float]
    started_at: datetime
    ended_at: Optional[datetime]
    config_snapshot: Optional[dict[str, Any]]
    room_id: UUID
    started_by_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

