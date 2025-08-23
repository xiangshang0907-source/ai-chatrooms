"""基础模型定义."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """所有模型的基类."""

    pass


class TimestampMixin:
    """时间戳混入类."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class BaseModel(Base, TimestampMixin):
    """包含通用字段的基础模型."""

    __abstract__ = True

    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid4
    )


class BaseEntity:
    """业务实体基类（非持久化）."""

    def __init__(self, **kwargs: Any) -> None:
        """初始化实体."""
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典."""
        result = {}
        for key, value in self.__dict__.items():
            if not key.startswith("_"):
                # 处理特殊类型转换
                if isinstance(value, UUID):
                    result[key] = str(value)
                elif isinstance(value, datetime):
                    result[key] = value.isoformat()
                else:
                    result[key] = value
        return result
