"""认证相关的API路由."""

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from ..auth import (
    create_tokens,
    get_current_user,
    hash_password,
    update_last_login,
    verify_password,
)
from ..database import get_db_session
from ..models import User, UserEntity, UserRole, UserStatus
from ..schemas.auth import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UpdateUserRequest,
    UserResponse,
)

auth_blueprint = Blueprint("auth", __name__, url_prefix="/auth")


@auth_blueprint.post("/register")
def register():
    """用户注册."""
    try:
        # 验证请求数据
        data = RegisterRequest(**request.get_json())
    except ValidationError as e:
        return {"error": "validation_error", "message": "请求数据无效", "details": e.errors()}, 400

    db_session = get_db_session()

    # 检查用户名和邮箱是否已存在
    existing_user = (
        db_session.query(User)
        .filter((User.username == data.username) | (User.email == data.email))
        .first()
    )

    if existing_user:
        if existing_user.username == data.username:
            return {"error": "username_exists", "message": "用户名已存在"}, 409
        else:
            return {"error": "email_exists", "message": "邮箱已存在"}, 409

    # 创建新用户
    try:
        user = User(
            username=data.username,
            email=data.email,
            password_hash=hash_password(data.password),
            display_name=data.display_name,
            status=UserStatus.ACTIVE,
            role=UserRole.USER,
            is_active=True,
        )

        db_session.add(user)
        db_session.commit()

        # 创建用户实体
        user_entity = UserEntity.from_model(user)

        # 创建令牌
        tokens = create_tokens(user_entity)

        # 更新最后登录时间
        update_last_login(str(user.id))

        # 构造响应
        auth_response = AuthResponse(
            **tokens,
            user=UserResponse.model_validate(user_entity.to_dict())
        )

        return auth_response.model_dump(), 201

    except IntegrityError:
        db_session.rollback()
        return {"error": "registration_failed", "message": "注册失败，请重试"}, 500


@auth_blueprint.post("/login")
def login():
    """用户登录."""
    try:
        # 验证请求数据
        data = LoginRequest(**request.get_json())
    except ValidationError as e:
        return {"error": "validation_error", "message": "请求数据无效", "details": e.errors()}, 400

    db_session = get_db_session()

    # 查找用户
    user = db_session.query(User).filter_by(username=data.username).first()

    if not user or not verify_password(data.password, user.password_hash):
        return {"error": "invalid_credentials", "message": "用户名或密码错误"}, 401

    # 检查用户状态
    if not user.is_active or user.status != UserStatus.ACTIVE:
        return {"error": "account_disabled", "message": "账户已被禁用"}, 401

    # 创建用户实体
    user_entity = UserEntity.from_model(user)

    # 创建令牌
    tokens = create_tokens(user_entity)

    # 更新最后登录时间
    update_last_login(str(user.id))

    # 构造响应
    auth_response = AuthResponse(
        **tokens,
        user=UserResponse.model_validate(user_entity.to_dict())
    )

    return auth_response.model_dump(), 200


@auth_blueprint.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    """刷新访问令牌."""
    user_id = get_jwt_identity()
    db_session = get_db_session()

    user = db_session.query(User).filter_by(id=user_id).first()
    if not user:
        return {"error": "user_not_found", "message": "用户不存在"}, 404

    # 检查用户状态
    if not user.is_active or user.status != UserStatus.ACTIVE:
        return {"error": "account_disabled", "message": "账户已被禁用"}, 401

    user_entity = UserEntity.from_model(user)
    tokens = create_tokens(user_entity)

    token_response = TokenResponse(
        access_token=tokens["access_token"],
        token_type=tokens["token_type"],
        expires_in=tokens["expires_in"]
    )

    return token_response.model_dump(), 200


@auth_blueprint.get("/me")
@jwt_required()
def get_current_user_info():
    """获取当前用户信息."""
    current_user = get_current_user()
    if not current_user:
        return {"error": "user_not_found", "message": "用户不存在"}, 404

    user_response = UserResponse.model_validate(current_user.to_dict())
    return user_response.model_dump(), 200


@auth_blueprint.patch("/me")
@jwt_required()
def update_current_user():
    """更新当前用户信息."""
    try:
        # 验证请求数据
        data = UpdateUserRequest(**request.get_json())
    except ValidationError as e:
        return {"error": "validation_error", "message": "请求数据无效", "details": e.errors()}, 400

    current_user = get_current_user()
    if not current_user:
        return {"error": "user_not_found", "message": "用户不存在"}, 404

    db_session = get_db_session()
    user = db_session.query(User).filter_by(id=current_user.id).first()

    if not user:
        return {"error": "user_not_found", "message": "用户不存在"}, 404

    # 更新用户信息
    if data.display_name is not None:
        user.display_name = data.display_name
    if data.avatar_url is not None:
        user.avatar_url = data.avatar_url

    try:
        db_session.commit()
        user_entity = UserEntity.from_model(user)
        user_response = UserResponse.model_validate(user_entity.to_dict())
        return user_response.model_dump(), 200

    except IntegrityError:
        db_session.rollback()
        return {"error": "update_failed", "message": "更新失败，请重试"}, 500
