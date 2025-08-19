"""用户相关模型."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .message import Message
    from .participant import Participant
    from .room import Room
from uuid import UUID

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseEntity, BaseModel


class UserStatus(str, Enum):
    """用户状态枚举."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    BANNED = "banned"


class UserRole(str, Enum):
    """用户角色枚举."""

    USER = "user"
    ADMIN = "admin"


class User(BaseModel):
    """用户模型."""

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    display_name: Mapped[str | None] = mapped_column(String(100))
    avatar_url: Mapped[str | None] = mapped_column(String(500))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[UserStatus] = mapped_column(String(20), default=UserStatus.ACTIVE)
    role: Mapped[UserRole] = mapped_column(String(20), default=UserRole.USER)

    last_login_at: Mapped[datetime | None] = mapped_column()

    # 关联关系
    owned_rooms: Mapped[list["Room"]] = relationship(
        "Room", back_populates="owner", cascade="all, delete-orphan"
    )
    participations: Mapped[list["Participant"]] = relationship(
        "Participant", back_populates="user", cascade="all, delete-orphan"
    )
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="author", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """字符串表示."""
        return f"<User(id={self.id}, username='{self.username}')>"


class UserEntity(BaseEntity):
    """用户业务实体."""

    def __init__(
        self,
        id: UUID,
        username: str,
        email: str,
        display_name: str | None = None,
        avatar_url: str | None = None,
        status: UserStatus = UserStatus.ACTIVE,
        role: UserRole = UserRole.USER,
        is_active: bool = True,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        last_login_at: datetime | None = None,
        **kwargs: Any,
    ) -> None:
        """初始化用户实体."""
        super().__init__(
            id=id,
            username=username,
            email=email,
            display_name=display_name,
            avatar_url=avatar_url,
            status=status,
            role=role,
            is_active=is_active,
            created_at=created_at,
            updated_at=updated_at,
            last_login_at=last_login_at,
            **kwargs,
        )

    @property
    def is_admin(self) -> bool:
        """是否为管理员."""
        return self.role == UserRole.ADMIN

    @property
    def can_login(self) -> bool:
        """是否可以登录."""
        return self.is_active and self.status == UserStatus.ACTIVE

    @classmethod
    def from_model(cls, user: User) -> "UserEntity":
        """从数据模型创建实体."""
        return cls(
            id=user.id,
            username=user.username,
            email=user.email,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            status=user.status,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login_at=user.last_login_at,
        )
