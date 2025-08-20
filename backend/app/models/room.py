"""房间相关模型."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .agent import AgentProfile
    from .conversation import ConversationRun
    from .message import Message
    from .participant import Participant
    from .user import User
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseEntity, BaseModel


class RoomStatus(str, Enum):
    """房间状态枚举."""

    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class Room(BaseModel):
    """房间模型."""

    __tablename__ = "rooms"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    status: Mapped[RoomStatus] = mapped_column(String(20), default=RoomStatus.ACTIVE)

    # 房间配置
    max_participants: Mapped[int] = mapped_column(Integer, default=10)
    allow_user_interruption: Mapped[bool] = mapped_column(default=True)
    max_rounds_per_session: Mapped[int] = mapped_column(Integer, default=50)
    round_timeout_seconds: Mapped[int] = mapped_column(Integer, default=300)

    # 扩展配置（JSON）
    settings: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    # 外键
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    # 关联关系
    owner: Mapped["User"] = relationship("User", back_populates="owned_rooms")
    participants: Mapped[list["Participant"]] = relationship(
        "Participant", back_populates="room", cascade="all, delete-orphan"
    )
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="room", cascade="all, delete-orphan"
    )
    runs: Mapped[list["ConversationRun"]] = relationship(
        "ConversationRun", back_populates="room", cascade="all, delete-orphan"
    )
    agent_profiles: Mapped[list["AgentProfile"]] = relationship(
        "AgentProfile", back_populates="room", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """字符串表示."""
        return f"<Room(id={self.id}, name='{self.name}')>"


class RoomEntity(BaseEntity):
    """房间业务实体."""

    def __init__(
        self,
        id: UUID,
        name: str,
        owner_id: UUID,
        description: str | None = None,
        status: RoomStatus = RoomStatus.ACTIVE,
        max_participants: int = 10,
        allow_user_interruption: bool = True,
        max_rounds_per_session: int = 50,
        round_timeout_seconds: int = 300,
        settings: dict[str, Any] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        **kwargs: Any,
    ) -> None:
        """初始化房间实体."""
        super().__init__(
            id=id,
            name=name,
            owner_id=owner_id,
            description=description,
            status=status,
            max_participants=max_participants,
            allow_user_interruption=allow_user_interruption,
            max_rounds_per_session=max_rounds_per_session,
            round_timeout_seconds=round_timeout_seconds,
            settings=settings or {},
            created_at=created_at,
            updated_at=updated_at,
            **kwargs,
        )

    @property
    def is_active(self) -> bool:
        """房间是否活跃."""
        return self.status == RoomStatus.ACTIVE

    @property
    def can_accept_participants(self) -> bool:
        """是否可以接受新参与者."""
        return self.is_active and len(getattr(self, "participants", [])) < self.max_participants

    @classmethod
    def from_model(cls, room: Room) -> "RoomEntity":
        """从数据模型创建实体."""
        return cls(
            id=room.id,
            name=room.name,
            owner_id=room.owner_id,
            description=room.description,
            status=room.status,
            max_participants=room.max_participants,
            allow_user_interruption=room.allow_user_interruption,
            max_rounds_per_session=room.max_rounds_per_session,
            round_timeout_seconds=room.round_timeout_seconds,
            settings=room.settings,
            created_at=room.created_at,
            updated_at=room.updated_at,
        )
