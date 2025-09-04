"""认证功能测试."""

import json

import pytest

from app import create_app
from app.auth import hash_password
from app.database import db
from app.models import User, UserRole, UserStatus


@pytest.fixture
def app():
    """创建测试应用."""
    app = create_app({
        "TESTING": True,
        "DATABASE_URL": "postgresql://postgres:postgres@localhost:5432/ai_chatrooms_test",
        "JWT_SECRET_KEY": "test-secret-key",
    })

    with app.app_context():
        # 创建测试数据库表
        db.create_all()
        yield app
        # 清理测试数据
        db.session.rollback()
        db.drop_all()


@pytest.fixture
def client(app):
    """创建测试客户端."""
    return app.test_client()


@pytest.fixture
def sample_user(app):
    """创建示例用户."""
    with app.app_context():
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=hash_password("password123"),
            display_name="Test User",
            status=UserStatus.ACTIVE,
            role=UserRole.USER,
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()
        return user


class TestUserRegistration:
    """用户注册测试."""

    def test_register_success(self, client):
        """测试成功注册."""
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123",
            "display_name": "New User"
        }

        response = client.post(
            "/auth/register",
            data=json.dumps(data),
            content_type="application/json"
        )

        assert response.status_code == 201
        response_data = response.get_json()

        assert "access_token" in response_data
        assert "refresh_token" in response_data
        assert response_data["token_type"] == "bearer"
        assert "user" in response_data
        assert response_data["user"]["username"] == "newuser"
        assert response_data["user"]["email"] == "newuser@example.com"

    def test_register_duplicate_username(self, client, sample_user):
        """测试重复用户名注册."""
        data = {
            "username": "testuser",  # 已存在的用户名
            "email": "different@example.com",
            "password": "password123"
        }

        response = client.post(
            "/auth/register",
            data=json.dumps(data),
            content_type="application/json"
        )

        assert response.status_code == 409
        response_data = response.get_json()
        assert response_data["error"] == "username_exists"

    def test_register_duplicate_email(self, client, sample_user):
        """测试重复邮箱注册."""
        data = {
            "username": "differentuser",
            "email": "test@example.com",  # 已存在的邮箱
            "password": "password123"
        }

        response = client.post(
            "/auth/register",
            data=json.dumps(data),
            content_type="application/json"
        )

        assert response.status_code == 409
        response_data = response.get_json()
        assert response_data["error"] == "email_exists"

    def test_register_invalid_data(self, client):
        """测试无效数据注册."""
        data = {
            "username": "ab",  # 太短
            "email": "invalid-email",  # 无效邮箱
            "password": "123"  # 太短
        }

        response = client.post(
            "/auth/register",
            data=json.dumps(data),
            content_type="application/json"
        )

        assert response.status_code == 400
        response_data = response.get_json()
        assert response_data["error"] == "validation_error"


class TestUserLogin:
    """用户登录测试."""

    def test_login_success(self, client, sample_user):
        """测试成功登录."""
        data = {
            "username": "testuser",
            "password": "password123"
        }

        response = client.post(
            "/auth/login",
            data=json.dumps(data),
            content_type="application/json"
        )

        assert response.status_code == 200
        response_data = response.get_json()

        assert "access_token" in response_data
        assert "refresh_token" in response_data
        assert response_data["token_type"] == "bearer"
        assert "user" in response_data
        assert response_data["user"]["username"] == "testuser"

    def test_login_invalid_username(self, client):
        """测试无效用户名登录."""
        data = {
            "username": "nonexistent",
            "password": "password123"
        }

        response = client.post(
            "/auth/login",
            data=json.dumps(data),
            content_type="application/json"
        )

        assert response.status_code == 401
        response_data = response.get_json()
        assert response_data["error"] == "invalid_credentials"

    def test_login_invalid_password(self, client, sample_user):
        """测试无效密码登录."""
        data = {
            "username": "testuser",
            "password": "wrongpassword"
        }

        response = client.post(
            "/auth/login",
            data=json.dumps(data),
            content_type="application/json"
        )

        assert response.status_code == 401
        response_data = response.get_json()
        assert response_data["error"] == "invalid_credentials"


class TestProtectedEndpoints:
    """受保护端点测试."""

    def test_get_current_user_success(self, client, sample_user):
        """测试获取当前用户信息成功."""
        # 先登录获取令牌
        login_data = {
            "username": "testuser",
            "password": "password123"
        }

        login_response = client.post(
            "/auth/login",
            data=json.dumps(login_data),
            content_type="application/json"
        )

        access_token = login_response.get_json()["access_token"]

        # 使用令牌访问受保护端点
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        response_data = response.get_json()
        assert response_data["username"] == "testuser"
        assert response_data["email"] == "test@example.com"

    def test_get_current_user_no_token(self, client):
        """测试无令牌访问受保护端点."""
        response = client.get("/auth/me")

        assert response.status_code == 401

    def test_update_user_info_success(self, client, sample_user):
        """测试更新用户信息成功."""
        # 先登录获取令牌
        login_data = {
            "username": "testuser",
            "password": "password123"
        }

        login_response = client.post(
            "/auth/login",
            data=json.dumps(login_data),
            content_type="application/json"
        )

        access_token = login_response.get_json()["access_token"]

        # 更新用户信息
        update_data = {
            "display_name": "Updated Test User",
            "avatar_url": "https://example.com/avatar.jpg"
        }

        response = client.patch(
            "/auth/me",
            data=json.dumps(update_data),
            content_type="application/json",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        response_data = response.get_json()
        assert response_data["display_name"] == "Updated Test User"
        assert response_data["avatar_url"] == "https://example.com/avatar.jpg"
