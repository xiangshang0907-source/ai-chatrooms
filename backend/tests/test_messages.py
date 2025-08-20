"""消息功能测试 - 使用PostgreSQL."""

import json
from uuid import uuid4

import pytest
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from flask import Flask
from flask.testing import FlaskClient

from app import create_app
from app.auth import create_tokens, hash_password
from app.database import db
from app.models.user import User, UserRole, UserStatus
from app.models.room import Room, RoomStatus
from app.models.participant import Participant, ParticipantStatus, ParticipantType


@pytest.fixture
def app() -> Flask:
    """创建测试应用 - 使用PostgreSQL."""
    # 创建测试数据库
    test_db_name = "ai_chatrooms_test_messages"
    
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
        "QWEN_API_KEY": "test-api-key",  # 测试用的API密钥
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
def test_user(app: Flask) -> str:
    """创建测试用户并返回用户ID."""
    with app.app_context():
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
        return str(test_user.id)


@pytest.fixture
def test_room(app: Flask) -> str:
    """创建测试房间并返回房间ID."""
    with app.app_context():
        # 直接在这里创建或获取用户
        user = db.session.query(User).filter(User.username == "testuser").first()
        if not user:
            user = User(
                username="testuser",
                email="test@example.com",
                password_hash=hash_password("testpass123"),
                display_name="Test User",
                is_active=True,
                status=UserStatus.ACTIVE,
                role=UserRole.USER,
            )
            db.session.add(user)
            db.session.flush()
        
        test_room = Room(
            name="测试聊天室",
            description="用于测试消息功能的房间",
            status=RoomStatus.ACTIVE,
            max_participants=10,
            allow_user_interruption=True,
            max_rounds_per_session=50,
            round_timeout_seconds=300,
            owner_id=user.id,
        )
        db.session.add(test_room)
        db.session.flush()
        
        # 创建用户参与者
        participant = Participant(
            type=ParticipantType.HUMAN,
            status=ParticipantStatus.ACTIVE,
            display_name=user.display_name or user.username,
            room_id=test_room.id,
            user_id=user.id,
        )
        db.session.add(participant)
        db.session.commit()
        
        return str(test_room.id)


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """创建测试客户端."""
    return app.test_client()


@pytest.fixture
def auth_headers(app: Flask, test_user: str) -> dict[str, str]:
    """创建认证头部."""
    with app.app_context():
        # 根据用户ID获取用户对象
        user = db.session.query(User).filter(User.id == test_user).first()
        tokens = create_tokens(user)
        return {"Authorization": f"Bearer {tokens['access_token']}"}


class TestMessageAPI:
    """消息API测试."""
    
    def test_send_message_success(
        self, 
        client: FlaskClient, 
        auth_headers: dict[str, str], 
        test_room: str
    ):
        """测试发送消息成功."""
        message_data = {
            "content": "Hello, this is a test message!",
        }
        
        response = client.post(
            f"/rooms/{test_room}/messages",
            data=json.dumps(message_data),
            content_type="application/json",
            headers=auth_headers,
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert "message_data" in data or "user_message" in data
        assert data["message"] == "消息发送成功"
    
    def test_send_message_unauthorized(self, client: FlaskClient, test_room: str):
        """测试未认证发送消息."""
        message_data = {"content": "Test message"}
        
        response = client.post(
            f"/rooms/{test_room}/messages",
            data=json.dumps(message_data),
            content_type="application/json",
        )
        
        assert response.status_code == 401
        data = response.get_json()
        assert "msg" in data  # JWT扩展返回的格式
    
    def test_send_message_to_nonexistent_room(
        self, 
        client: FlaskClient, 
        auth_headers: dict[str, str]
    ):
        """测试发送消息到不存在的房间."""
        room_id = str(uuid4())
        message_data = {"content": "Test message"}
        
        response = client.post(
            f"/rooms/{room_id}/messages",
            data=json.dumps(message_data),
            content_type="application/json",
            headers=auth_headers,
        )
        
        assert response.status_code == 404
        data = response.get_json()
        assert data["error"] == "room_not_found"
    
    def test_get_messages_success(
        self, 
        client: FlaskClient, 
        auth_headers: dict[str, str], 
        test_room: str
    ):
        """测试获取消息历史成功."""
        # 先发送一条消息
        message_data = {"content": "Test message for history"}
        client.post(
            f"/rooms/{test_room}/messages",
            data=json.dumps(message_data),
            content_type="application/json",
            headers=auth_headers,
        )
        
        # 获取消息历史
        response = client.get(
            f"/rooms/{test_room}/messages",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert "messages" in data
        assert "total" in data
        assert "page" in data
        assert isinstance(data["messages"], list)
    
    def test_get_messages_unauthorized(self, client: FlaskClient, test_room: str):
        """测试未认证获取消息历史."""
        response = client.get(f"/rooms/{test_room}/messages")
        
        assert response.status_code == 401
        data = response.get_json()
        assert "msg" in data  # JWT扩展返回的格式
    
    def test_start_conversation_success(
        self, 
        client: FlaskClient, 
        auth_headers: dict[str, str], 
        test_room: str
    ):
        """测试开始对话成功."""
        conversation_data = {
            "name": "测试对话",
            "description": "这是一个测试对话",
        }
        
        response = client.post(
            f"/rooms/{test_room}/conversations",
            data=json.dumps(conversation_data),
            content_type="application/json",
            headers=auth_headers,
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data["name"] == conversation_data["name"]
        assert data["description"] == conversation_data["description"]
        assert data["status"] == "running"
        assert "id" in data


class TestMessageValidation:
    """消息数据验证测试."""
    
    def test_send_empty_message(
        self, 
        client: FlaskClient, 
        auth_headers: dict[str, str], 
        test_room: str
    ):
        """测试发送空消息."""
        message_data = {"content": ""}
        
        response = client.post(
            f"/rooms/{test_room}/messages",
            data=json.dumps(message_data),
            content_type="application/json",
            headers=auth_headers,
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data["error"] == "validation_error"
    
    def test_send_too_long_message(
        self, 
        client: FlaskClient, 
        auth_headers: dict[str, str], 
        test_room: str
    ):
        """测试发送过长消息."""
        # 创建超过10000字符的消息
        long_content = "A" * 10001
        message_data = {"content": long_content}
        
        response = client.post(
            f"/rooms/{test_room}/messages",
            data=json.dumps(message_data),
            content_type="application/json",
            headers=auth_headers,
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data["error"] == "validation_error"
