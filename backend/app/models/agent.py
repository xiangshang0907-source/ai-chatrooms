"""AI代理相关模型."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .participant import Participant
    from .room import Room
    from .user import User
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseEntity, BaseModel


class ProviderType(str, Enum):
    """LLM提供商类型枚举."""

    QWEN = "qwen"
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    BEDROCK = "bedrock"
    LOCAL = "local"


class AgentProfile(BaseModel):
    """AI代理配置模型."""

    __tablename__ = "agent_profiles"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # AI配置
    provider: Mapped[ProviderType] = mapped_column(
        String(20), default=ProviderType.QWEN
    )
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    system_prompt: Mapped[str | None] = mapped_column(Text)

    # 生成参数
    temperature: Mapped[float | None] = mapped_column(default=0.7)
    max_tokens: Mapped[int | None] = mapped_column(Integer, default=2000)
    top_p: Mapped[float | None] = mapped_column(default=0.95)

    # 扩展配置
    config: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    # 工具权限配置
    allowed_tools: Mapped[list[str] | None] = mapped_column(JSONB)

    # 外键
    room_id: Mapped[UUID] = mapped_column(ForeignKey("rooms.id"), nullable=False)
    created_by_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    # 关联关系
    room: Mapped["Room"] = relationship("Room", back_populates="agent_profiles")
    created_by: Mapped["User"] = relationship("User")
    participants: Mapped[list["Participant"]] = relationship(
        "Participant", back_populates="agent_profile", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """字符串表示."""
        return f"<AgentProfile(id={self.id}, name='{self.name}')>"


class AgentProfileEntity(BaseEntity):
    """AI代理配置业务实体."""

    def __init__(
        self,
        id: UUID,
        name: str,
        room_id: UUID,
        created_by_id: UUID,
        model_name: str,
        provider: ProviderType = ProviderType.QWEN,
        description: str | None = None,
        system_prompt: str | None = None,
        temperature: float | None = 0.7,
        max_tokens: int | None = 2000,
        top_p: float | None = 0.95,
        config: dict[str, Any] | None = None,
        allowed_tools: list[str] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        **kwargs: Any,
    ) -> None:
        """初始化代理配置实体."""
        super().__init__(
            id=id,
            name=name,
            room_id=room_id,
            created_by_id=created_by_id,
            model_name=model_name,
            provider=provider,
            description=description,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            config=config or {},
            allowed_tools=allowed_tools or [],
            created_at=created_at,
            updated_at=updated_at,
            **kwargs,
        )

    @property
    def full_model_identifier(self) -> str:
        """完整的模型标识符."""
        return f"{self.provider}:{self.model_name}"

    @property
    def generation_config(self) -> dict[str, Any]:
        """生成配置字典."""
        config = {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
        }
        # 移除 None 值
        return {k: v for k, v in config.items() if v is not None}

    @classmethod
    def from_model(cls, agent: AgentProfile) -> "AgentProfileEntity":
        """从数据模型创建实体."""
        return cls(
            id=agent.id,
            name=agent.name,
            room_id=agent.room_id,
            created_by_id=agent.created_by_id,
            model_name=agent.model_name,
            provider=agent.provider,
            description=agent.description,
            system_prompt=agent.system_prompt,
            temperature=agent.temperature,
            max_tokens=agent.max_tokens,
            top_p=agent.top_p,
            config=agent.config,
            allowed_tools=agent.allowed_tools,
            created_at=agent.created_at,
            updated_at=agent.updated_at,
        )
