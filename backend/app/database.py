"""数据库连接与初始化."""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from .models.base import Base

# 创建 SQLAlchemy 实例
db = SQLAlchemy(model_class=Base)


def init_db(app: Flask) -> None:
    """初始化数据库连接."""
    # 配置数据库 URI
    app.config["SQLALCHEMY_DATABASE_URI"] = app.config["DATABASE_URL"]
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ECHO"] = app.config.get("SQLALCHEMY_ECHO", "false").lower() == "true"

    # 初始化 SQLAlchemy
    db.init_app(app)

    # 在应用上下文中创建所有表（仅在非测试环境）
    with app.app_context():
        if not app.config.get("TESTING"):
            # 导入所有模型以确保它们被注册
            from .models import (  # noqa: F401
                AgentProfile,
                ConversationRun,
                Message,
                Participant,
                Room,
                User,
            )

            # 创建所有表
            db.create_all()


def get_db_session():
    """获取数据库会话."""
    return db.session

