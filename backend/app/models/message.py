"""消息相关模型."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from .conversation import ConversationRun
    from .participant import Participant
    from .room import Room
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseEntity, BaseModel


class MessageType(str, Enum):
    """消息类型枚举."""

    TEXT = "text"
    SYSTEM = "system"
    ERROR = "error"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"


class MessageStatus(str, Enum):
    """消息状态枚举."""

    SENT = "sent"
    GENERATING = "generating"  # AI生成中状态
    DELIVERED = "delivered"
    READ = "read"
    EDITED = "edited"
    DELETED = "deleted"


class Message(BaseModel):
    """消息模型."""

    __tablename__ = "messages"

    content: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[MessageType] = mapped_column(String(20), default=MessageType.TEXT)
    status: Mapped[MessageStatus] = mapped_column(String(20), default=MessageStatus.SENT)

    # 序号（在房间内的消息顺序）
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # 回复相关
    reply_to_id: Mapped[UUID | None] = mapped_column(ForeignKey("messages.id"))

    # 扩展数据（如工具调用参数、结果等）
    extra_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    # 外键
    room_id: Mapped[UUID] = mapped_column(ForeignKey("rooms.id"), nullable=False)
    participant_id: Mapped[UUID] = mapped_column(
        ForeignKey("participants.id"), nullable=False
    )
    run_id: Mapped[UUID | None] = mapped_column(ForeignKey("conversation_runs.id"))

    # 关联关系
    room: Mapped["Room"] = relationship("Room", back_populates="messages")
    participant: Mapped["Participant"] = relationship(
        "Participant", back_populates="messages"
    )
    run: Mapped[Optional["ConversationRun"]] = relationship(
        "ConversationRun", back_populates="messages"
    )
    reply_to: Mapped[Optional["Message"]] = relationship(
        "Message", remote_side="Message.id"
    )

    def __repr__(self) -> str:
        """字符串表示."""
        content_preview = (
            self.content[:50] + "..." if len(self.content) > 50 else self.content
        )
        return f"<Message(id={self.id}, type={self.type}, content='{content_preview}')>"


class MessageEntity(BaseEntity):
    """消息业务实体."""

    def __init__(
        self,
        id: UUID,
        content: str,
        room_id: UUID,
        participant_id: UUID,
        sequence_number: int,
        type: MessageType = MessageType.TEXT,
        status: MessageStatus = MessageStatus.SENT,
        reply_to_id: UUID | None = None,
        run_id: UUID | None = None,
        extra_data: dict[str, Any] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        **kwargs: Any,
    ) -> None:
        """初始化消息实体."""
        super().__init__(
            id=id,
            content=content,
            room_id=room_id,
            participant_id=participant_id,
            sequence_number=sequence_number,
            type=type,
            status=status,
            reply_to_id=reply_to_id,
            run_id=run_id,
            extra_data=extra_data or {},
            created_at=created_at,
            updated_at=updated_at,
            **kwargs,
        )

    @property
    def is_reply(self) -> bool:
        """是否为回复消息."""
        return self.reply_to_id is not None

    @property
    def is_system_message(self) -> bool:
        """是否为系统消息."""
        return self.type == MessageType.SYSTEM

    @property
    def is_tool_related(self) -> bool:
        """是否与工具调用相关."""
        return self.type in [MessageType.TOOL_CALL, MessageType.TOOL_RESULT]

    @property
    def content_preview(self) -> str:
        """内容预览（截断长文本）."""
        if len(self.content) <= 100:
            return self.content
        return self.content[:97] + "..."

    @classmethod
    def from_model(cls, message: Message) -> "MessageEntity":
        """从数据模型创建实体."""
        return cls(
            id=message.id,
            content=message.content,
            room_id=message.room_id,
            participant_id=message.participant_id,
            sequence_number=message.sequence_number,
            type=message.type,
            status=message.status,
            reply_to_id=message.reply_to_id,
            run_id=message.run_id,
            extra_data=message.extra_data,
            created_at=message.created_at,
            updated_at=message.updated_at,
        )
