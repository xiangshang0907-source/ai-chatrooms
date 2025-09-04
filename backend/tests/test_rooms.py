"""房间功能测试."""

import json
from uuid import uuid4

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app import create_app
from app.auth import create_tokens, hash_password
from app.database import db
from app.models.user import User, UserRole, UserStatus


@pytest.fixture
def app() -> Flask:
    """创建测试应用."""
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

    # 创建测试数据库
    test_db_name = "ai_chatrooms_test_rooms"

    # 连接到默认数据库创建测试数据库
    try:
        conn = psycopg2.connect(
            "postgresql://postgres:postgres@localhost:5432/postgres"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # 删除测试数据库（如果存在）
        cursor.execute(f"DROP DATABASE IF EXISTS {test_db_name}")
        # 创建测试数据库
        cursor.execute(f"CREATE DATABASE {test_db_name}")

        cursor.close()
        conn.close()
    except psycopg2.OperationalError:
        # 如果PostgreSQL不可用，跳过这些测试
        pytest.skip("PostgreSQL server not available")

    # 创建应用并连接到测试数据库
    app = create_app({
        "TESTING": True,
        "DATABASE_URL": f"postgresql://postgres:postgres@localhost:5432/{test_db_name}",
        "JWT_SECRET_KEY": "test-secret-key",
    })

    with app.app_context():
        # 创建所有数据库表
        from app.models.base import Base
        Base.metadata.create_all(db.engine)

        yield app

        # 清理：删除测试数据库
        try:
            db.session.close()
            db.engine.dispose()

            conn = psycopg2.connect(
                "postgresql://postgres:postgres@localhost:5432/postgres"
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            cursor.execute(f"DROP DATABASE IF EXISTS {test_db_name}")
            cursor.close()
            conn.close()
        except:
            pass  # 忽略清理错误


@pytest.fixture
def test_user(app: Flask) -> User:
    """创建测试用户."""
    with app.app_context():
        # 检查用户是否已存在
        existing_user = db.session.query(User).filter_by(username="testuser").first()
        if existing_user:
            return existing_user

        # 创建新用户
        test_user = User(
            username="testuser",
            email="test@example.com",
            password_hash=hash_password("testpass123"),
            display_name="Test User",
            is_active=True,
            status=UserStatus.ACTIVE,
            role=UserRole.USER,
        )
        db.session.add(test_user)
        db.session.commit()
        return test_user


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """创建测试客户端."""
    return app.test_client()


@pytest.fixture
def auth_headers(app: Flask, test_user: User) -> dict[str, str]:
    """创建认证头部."""
    with app.app_context():
        # 重新获取用户对象以确保会话绑定
        user = db.session.merge(test_user)
        db.session.refresh(user)
        tokens = create_tokens(user.id)
        return {"Authorization": f"Bearer {tokens['access_token']}"}


class TestRoomBasicAPI:
    """房间基础API测试."""

    def test_create_room_success(self, client: FlaskClient, auth_headers: dict[str, str]):
        """测试创建房间成功."""
        room_data = {
            "name": "测试房间",
            "description": "这是一个测试房间",
            "max_participants": 5,
            "allow_user_interruption": True,
        }

        response = client.post(
            "/rooms",
            data=json.dumps(room_data),
            content_type="application/json",
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["name"] == room_data["name"]
        assert data["description"] == room_data["description"]
        assert data["max_participants"] == room_data["max_participants"]
        assert "id" in data
        assert "created_at" in data

    def test_create_room_unauthorized(self, client: FlaskClient):
        """测试未认证创建房间."""
        room_data = {"name": "测试房间"}

        response = client.post(
            "/rooms",
            data=json.dumps(room_data),
            content_type="application/json",
        )

        assert response.status_code == 401

    def test_create_room_invalid_data(self, client: FlaskClient, auth_headers: dict[str, str]):
        """测试创建房间数据验证."""
        # 房间名称为空
        room_data = {"name": ""}

        response = client.post(
            "/rooms",
            data=json.dumps(room_data),
            content_type="application/json",
            headers=auth_headers,
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["error"] == "validation_error"

    def test_get_rooms_list(self, client: FlaskClient, auth_headers: dict[str, str]):
        """测试获取房间列表."""
        response = client.get("/rooms", headers=auth_headers)

        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.get_json()}")
            print(f"Response text: {response.get_data(as_text=True)}")

        assert response.status_code == 200
        data = response.get_json()
        assert "rooms" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "has_next" in data
        assert isinstance(data["rooms"], list)

    def test_get_room_not_found(self, client: FlaskClient):
        """测试获取不存在的房间."""
        room_id = str(uuid4())
        response = client.get(f"/rooms/{room_id}")

        assert response.status_code == 404
        data = response.get_json()
        assert data["error"] == "not_found"


class TestRoomPermissions:
    """房间权限测试."""

    def test_update_room_by_owner(self, client: FlaskClient, auth_headers: dict[str, str]):
        """测试房主更新房间."""
        # 先创建房间
        room_data = {"name": "原始房间名称"}
        create_response = client.post(
            "/rooms",
            data=json.dumps(room_data),
            content_type="application/json",
            headers=auth_headers,
        )
        assert create_response.status_code == 201
        room_id = create_response.get_json()["id"]

        # 更新房间
        update_data = {"name": "更新后的房间名称"}
        response = client.patch(
            f"/rooms/{room_id}",
            data=json.dumps(update_data),
            content_type="application/json",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["name"] == update_data["name"]

    def test_delete_room_by_owner(self, client: FlaskClient, auth_headers: dict[str, str]):
        """测试房主删除房间."""
        # 先创建房间
        room_data = {"name": "待删除房间"}
        create_response = client.post(
            "/rooms",
            data=json.dumps(room_data),
            content_type="application/json",
            headers=auth_headers,
        )
        assert create_response.status_code == 201
        room_id = create_response.get_json()["id"]

        # 删除房间
        response = client.delete(f"/rooms/{room_id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data["message"] == "房间删除成功"
        assert data["room_id"] == room_id


class TestRoomParticipation:
    """房间参与测试."""

    def test_join_room_success(self, client: FlaskClient, auth_headers: dict[str, str]):
        """测试加入房间成功."""
        # 先创建房间
        room_data = {"name": "测试加入房间"}
        create_response = client.post(
            "/rooms",
            data=json.dumps(room_data),
            content_type="application/json",
            headers=auth_headers,
        )
        assert create_response.status_code == 201
        room_id = create_response.get_json()["id"]

        # 加入房间（房主已自动加入，这里测试重复加入）
        join_data = {"display_name": "测试用户"}
        response = client.post(
            f"/rooms/{room_id}/join",
            data=json.dumps(join_data),
            content_type="application/json",
            headers=auth_headers,
        )

        # 应该返回已经在房间中的错误
        assert response.status_code == 400
        data = response.get_json()
        assert data["error"] == "already_joined"

    def test_join_nonexistent_room(self, client: FlaskClient, auth_headers: dict[str, str]):
        """测试加入不存在的房间."""
        room_id = str(uuid4())
        response = client.post(
            f"/rooms/{room_id}/join",
            data=json.dumps({}),
            content_type="application/json",
            headers=auth_headers,
        )

        assert response.status_code == 404
        data = response.get_json()
        assert data["error"] == "not_found"

    def test_leave_room_success(self, client: FlaskClient, auth_headers: dict[str, str]):
        """测试离开房间（房主无法离开）."""
        # 先创建房间
        room_data = {"name": "测试离开房间"}
        create_response = client.post(
            "/rooms",
            data=json.dumps(room_data),
            content_type="application/json",
            headers=auth_headers,
        )
        assert create_response.status_code == 201
        room_id = create_response.get_json()["id"]

        # 尝试离开房间（房主应该不能离开）
        response = client.post(f"/rooms/{room_id}/leave", headers=auth_headers)

        assert response.status_code == 400
        data = response.get_json()
        assert data["error"] == "owner_cannot_leave"
