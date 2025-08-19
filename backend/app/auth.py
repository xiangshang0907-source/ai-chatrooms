"""JWT认证相关功能."""

from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Optional

import bcrypt
from flask import current_app
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
    verify_jwt_in_request,
)

from .database import get_db_session
from .models import User, UserEntity

jwt = JWTManager()


def init_jwt(app) -> None:
    """初始化JWT配置."""
    app.config["JWT_SECRET_KEY"] = app.config["JWT_SECRET_KEY"]
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(
        seconds=app.config["JWT_ACCESS_TOKEN_EXPIRES"]
    )
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(
        seconds=app.config["JWT_REFRESH_TOKEN_EXPIRES"]
    )

    jwt.init_app(app)

    @jwt.user_identity_loader
    def user_identity_lookup(user: UserEntity) -> str:
        """用户身份加载器."""
        return str(user.id)

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_payload) -> UserEntity | None:
        """用户查找回调."""
        identity = jwt_payload["sub"]
        db_session = get_db_session()
        user = db_session.query(User).filter_by(id=identity).first()
        return UserEntity.from_model(user) if user else None


def hash_password(password: str) -> str:
    """哈希密码."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """验证密码."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def create_tokens(user: UserEntity) -> dict[str, Any]:
    """为用户创建访问令牌和刷新令牌."""
    access_token = create_access_token(identity=user)
    refresh_token = create_refresh_token(identity=user)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": current_app.config["JWT_ACCESS_TOKEN_EXPIRES"].total_seconds(),
    }


def get_current_user() -> UserEntity | None:
    """获取当前用户."""
    try:
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        if not user_id:
            return None

        db_session = get_db_session()
        user = db_session.query(User).filter_by(id=user_id).first()
        return UserEntity.from_model(user) if user else None
    except Exception:
        return None


def login_required(f):
    """登录要求装饰器."""

    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """管理员权限要求装饰器."""

    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user = get_current_user()
        if not current_user or not current_user.is_admin:
            return {"error": "admin_required", "message": "需要管理员权限"}, 403
        return f(*args, **kwargs)

    return decorated_function


def update_last_login(user_id: str) -> None:
    """更新用户最后登录时间."""
    db_session = get_db_session()
    user = db_session.query(User).filter_by(id=user_id).first()
    if user:
        user.last_login_at = datetime.utcnow()
        db_session.commit()

