"""对话运行相关模型."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .message import Message
    from .room import Room
    from .user import User
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseEntity, BaseModel


class RunStatus(str, Enum):
    """对话运行状态枚举."""

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ConversationRun(BaseModel):
    """对话运行模型（一次完整的多轮对话会话）."""

    __tablename__ = "conversation_runs"

    name: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)

    status: Mapped[RunStatus] = mapped_column(String(20), default=RunStatus.PENDING)

    # 运行统计
    total_rounds: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost: Mapped[float | None] = mapped_column(default=0.0)

    # 运行时间
    started_at: Mapped[datetime | None] = mapped_column()
    ended_at: Mapped[datetime | None] = mapped_column()

    # 配置快照（运行时的房间配置）
    config_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    # 错误信息
    error_message: Mapped[str | None] = mapped_column(Text)

    # 外键
    room_id: Mapped[UUID] = mapped_column(ForeignKey("rooms.id"), nullable=False)
    started_by_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    # 关联关系
    room: Mapped["Room"] = relationship("Room", back_populates="runs")
    started_by: Mapped["User"] = relationship("User")
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="run", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """字符串表示."""
        return f"<ConversationRun(id={self.id}, status={self.status}, rounds={self.total_rounds})>"


class ConversationRunEntity(BaseEntity):
    """对话运行业务实体."""

    def __init__(
        self,
        id: UUID,
        room_id: UUID,
        started_by_id: UUID,
        status: RunStatus = RunStatus.PENDING,
        name: str | None = None,
        description: str | None = None,
        total_rounds: int = 0,
        total_tokens_used: int = 0,
        estimated_cost: float | None = 0.0,
        started_at: datetime | None = None,
        ended_at: datetime | None = None,
        config_snapshot: dict[str, Any] | None = None,
        error_message: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        **kwargs: Any,
    ) -> None:
        """初始化对话运行实体."""
        super().__init__(
            id=id,
            room_id=room_id,
            started_by_id=started_by_id,
            status=status,
            name=name,
            description=description,
            total_rounds=total_rounds,
            total_tokens_used=total_tokens_used,
            estimated_cost=estimated_cost,
            started_at=started_at,
            ended_at=ended_at,
            config_snapshot=config_snapshot or {},
            error_message=error_message,
            created_at=created_at,
            updated_at=updated_at,
            **kwargs,
        )

    @property
    def is_active(self) -> bool:
        """是否正在运行."""
        return self.status in [RunStatus.PENDING, RunStatus.RUNNING]

    @property
    def is_finished(self) -> bool:
        """是否已结束."""
        return self.status in [
            RunStatus.COMPLETED,
            RunStatus.FAILED,
            RunStatus.CANCELLED,
        ]

    @property
    def duration_seconds(self) -> float | None:
        """运行时长（秒）."""
        if self.started_at is None:
            return None
        end_time = self.ended_at or datetime.utcnow()
        return (end_time - self.started_at).total_seconds()

    @property
    def average_tokens_per_round(self) -> float:
        """平均每轮token使用量."""
        if self.total_rounds == 0:
            return 0.0
        return self.total_tokens_used / self.total_rounds

    @classmethod
    def from_model(cls, run: ConversationRun) -> "ConversationRunEntity":
        """从数据模型创建实体."""
        return cls(
            id=run.id,
            room_id=run.room_id,
            started_by_id=run.started_by_id,
            status=run.status,
            name=run.name,
            description=run.description,
            total_rounds=run.total_rounds,
            total_tokens_used=run.total_tokens_used,
            estimated_cost=run.estimated_cost,
            started_at=run.started_at,
            ended_at=run.ended_at,
            config_snapshot=run.config_snapshot,
            error_message=run.error_message,
            created_at=run.created_at,
            updated_at=run.updated_at,
        )
