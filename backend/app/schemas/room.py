"""房间相关的数据模式定义."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from ..models.room import RoomStatus
from ..models.participant import ParticipantType, ParticipantStatus


class RoomCreateRequest(BaseModel):
    """创建房间请求."""
    
    name: str = Field(..., min_length=1, max_length=100, description="房间名称")
    description: Optional[str] = Field(None, max_length=500, description="房间描述")
    max_participants: int = Field(10, ge=2, le=100, description="最大参与者数量")
    allow_user_interruption: bool = Field(True, description="是否允许用户打断")
    max_rounds_per_session: int = Field(50, ge=1, le=1000, description="每个会话最大轮数")
    round_timeout_seconds: int = Field(300, ge=30, le=3600, description="轮次超时时间（秒）")
    settings: Optional[dict[str, Any]] = Field(None, description="扩展设置")


class RoomUpdateRequest(BaseModel):
    """更新房间请求."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="房间名称")
    description: Optional[str] = Field(None, max_length=500, description="房间描述")
    status: Optional[RoomStatus] = Field(None, description="房间状态")
    max_participants: Optional[int] = Field(None, ge=2, le=100, description="最大参与者数量")
    allow_user_interruption: Optional[bool] = Field(None, description="是否允许用户打断")
    max_rounds_per_session: Optional[int] = Field(None, ge=1, le=1000, description="每个会话最大轮数")
    round_timeout_seconds: Optional[int] = Field(None, ge=30, le=3600, description="轮次超时时间（秒）")
    settings: Optional[dict[str, Any]] = Field(None, description="扩展设置")


class ParticipantResponse(BaseModel):
    """参与者响应."""
    
    id: UUID
    type: ParticipantType
    status: ParticipantStatus
    display_name: str
    room_id: UUID
    user_id: Optional[UUID]
    agent_profile_id: Optional[UUID]
    created_at: datetime

    class Config:
        from_attributes = True


class RoomResponse(BaseModel):
    """房间响应."""
    
    id: UUID
    name: str
    description: Optional[str]
    status: RoomStatus
    max_participants: int
    allow_user_interruption: bool
    max_rounds_per_session: int
    round_timeout_seconds: int
    settings: Optional[dict[str, Any]]
    owner_id: UUID
    created_at: datetime
    updated_at: datetime
    
    # 参与者数量（可选，用于列表显示）
    participant_count: Optional[int] = None
    
    class Config:
        from_attributes = True


class RoomDetailResponse(RoomResponse):
    """房间详情响应（包含参与者列表）."""
    
    participants: list[ParticipantResponse] = []


class RoomListResponse(BaseModel):
    """房间列表响应."""
    
    rooms: list[RoomResponse]
    total: int
    page: int
    page_size: int
    has_next: bool


class JoinRoomRequest(BaseModel):
    """加入房间请求."""
    
    display_name: Optional[str] = Field(None, max_length=100, description="显示名称（可选）")


class JoinRoomResponse(BaseModel):
    """加入房间响应."""
    
    participant: ParticipantResponse
    room: RoomResponse
    message: str


class LeaveRoomResponse(BaseModel):
    """离开房间响应."""
    
    message: str
    room_id: UUID

