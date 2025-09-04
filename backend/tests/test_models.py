"""简化的测试模型."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.models.user import UserRole, UserStatus


class MockBase(DeclarativeBase):
    """独立的测试基类."""

    pass


class SimpleUser(MockBase):
    """简化的测试用户模型（无关系）."""

    __tablename__ = "test_users"

    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[UserStatus] = mapped_column(String(20), default=UserStatus.ACTIVE)
    role: Mapped[UserRole] = mapped_column(String(20), default=UserRole.USER)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        """字符串表示."""
        return f"<SimpleUser(id={self.id}, username='{self.username}')>"
