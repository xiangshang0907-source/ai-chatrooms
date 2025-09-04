"""简化的认证功能测试."""

import json

import pytest

from app import create_app


@pytest.fixture
def app():
    """创建测试应用."""
    app = create_app({
        "TESTING": True,
        "DATABASE_URL": "sqlite:///:memory:",
        "JWT_SECRET_KEY": "test-secret-key",
    })
    return app


@pytest.fixture
def client(app):
    """创建测试客户端."""
    return app.test_client()


class TestBasicAuth:
    """基础认证测试."""

    def test_health_endpoint(self, client):
        """测试健康检查端点."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.get_json()
        assert data["status"] == "ok"
        assert data["service"] == "ai-chatrooms"

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

    def test_login_invalid_data(self, client):
        """测试无效数据登录."""
        data = {
            "username": "",  # 空用户名
            "password": ""   # 空密码
        }

        response = client.post(
            "/auth/login",
            data=json.dumps(data),
            content_type="application/json"
        )

        assert response.status_code == 400
        response_data = response.get_json()
        assert response_data["error"] == "validation_error"

    def test_protected_endpoint_no_token(self, client):
        """测试无令牌访问受保护端点."""
        response = client.get("/auth/me")
        assert response.status_code == 401
