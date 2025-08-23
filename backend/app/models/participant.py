"""参与者相关模型."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from .agent import AgentProfile
    from .message import Message
    from .room import Room
    from .user import User
from uuid import UUID

from sqlalchemy import ForeignKey, String, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseEntity, BaseModel


class ParticipantType(str, Enum):
    """参与者类型枚举."""

    HUMAN = "human"
    AGENT = "agent"


class ParticipantStatus(str, Enum):
    """参与者状态枚举."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    MUTED = "muted"


class Participant(BaseModel):
    """参与者模型."""

    __tablename__ = "participants"

    type: Mapped[ParticipantType] = mapped_column(
        String(20), nullable=False, default=ParticipantType.HUMAN
    )
    status: Mapped[ParticipantStatus] = mapped_column(
        String(20), default=ParticipantStatus.ACTIVE
    )

    # 显示名称（可能与用户名或代理名不同）
    display_name: Mapped[str | None] = mapped_column(String(100))

    # 外键
    room_id: Mapped[UUID] = mapped_column(ForeignKey("rooms.id"), nullable=False)
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    agent_profile_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("agent_profiles.id")
    )

    # 关联关系
    room: Mapped["Room"] = relationship("Room", back_populates="participants")
    user: Mapped[Optional["User"]] = relationship("User", back_populates="participations")
    agent_profile: Mapped[Optional["AgentProfile"]] = relationship(
        "AgentProfile", back_populates="participants"
    )
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="participant", cascade="all, delete-orphan"
    )

    # 唯一约束：同一房间中，同一用户或代理只能有一个活跃参与
    # 使用部分索引来处理NULL值
    __table_args__ = (
        Index("idx_room_user_unique", "room_id", "user_id", unique=True, 
              postgresql_where="user_id IS NOT NULL"),
        Index("idx_room_agent_unique", "room_id", "agent_profile_id", unique=True,
              postgresql_where="agent_profile_id IS NOT NULL"),
    )

    def __repr__(self) -> str:
        """字符串表示."""
        return f"<Participant(id={self.id}, type={self.type}, room_id={self.room_id})>"


class ParticipantEntity(BaseEntity):
    """参与者业务实体."""

    def __init__(
        self,
        id: UUID,
        room_id: UUID,
        type: ParticipantType,
        status: ParticipantStatus = ParticipantStatus.ACTIVE,
        display_name: str | None = None,
        user_id: UUID | None = None,
        agent_profile_id: UUID | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        **kwargs: Any,
    ) -> None:
        """初始化参与者实体."""
        super().__init__(
            id=id,
            room_id=room_id,
            type=type,
            status=status,
            display_name=display_name,
            user_id=user_id,
            agent_profile_id=agent_profile_id,
            created_at=created_at,
            updated_at=updated_at,
            **kwargs,
        )

    @property
    def is_human(self) -> bool:
        """是否为人类参与者."""
        return self.type == ParticipantType.HUMAN

    @property
    def is_agent(self) -> bool:
        """是否为AI代理."""
        return self.type == ParticipantType.AGENT

    @property
    def is_active(self) -> bool:
        """是否活跃."""
        return self.status == ParticipantStatus.ACTIVE

    @property
    def can_speak(self) -> bool:
        """是否可以发言."""
        return self.is_active and self.status != ParticipantStatus.MUTED

    @classmethod
    def from_model(cls, participant: Participant) -> "ParticipantEntity":
        """从数据模型创建实体."""
        return cls(
            id=participant.id,
            room_id=participant.room_id,
            type=participant.type,
            status=participant.status,
            display_name=participant.display_name,
            user_id=participant.user_id,
            agent_profile_id=participant.agent_profile_id,
            created_at=participant.created_at,
            updated_at=participant.updated_at,
        )
