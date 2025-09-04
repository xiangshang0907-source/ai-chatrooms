"""Message functionality tests using PostgreSQL."""

import json
from uuid import uuid4

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app.database import db
from app.models.participant import Participant, ParticipantStatus, ParticipantType
from app.models.room import Room, RoomStatus
from app.models.user import User, UserRole, UserStatus


# Test fixtures are now provided by conftest.py


@pytest.fixture
def test_room(app: Flask, test_user: User) -> str:
    """Create test room and return room ID."""
    with app.app_context():
        user = db.session.merge(test_user)
        db.session.refresh(user)
        
        test_room = Room(
            name="Test Chat Room",
            description="Room for testing message functionality",
            status=RoomStatus.ACTIVE,
            max_participants=10,
            allow_user_interruption=True,
            max_rounds_per_session=50,
            round_timeout_seconds=300,
            owner_id=user.id,
        )
        db.session.add(test_room)
        db.session.flush()

        # Create user participant
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


# Client and auth_headers fixtures are now provided by conftest.py


class TestMessageAPI:
    """Message API tests."""

    def test_send_message_success(
        self,
        client: FlaskClient,
        auth_headers: dict[str, str],
        test_room: str
    ):
        """Test sending message successfully."""
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
        assert "message" in data and ("消息发送成功" in data["message"] or "success" in data["message"].lower())

    def test_send_message_unauthorized(self, client: FlaskClient, test_room: str):
        """Test sending message without authentication."""
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
        """Test sending message to non-existent room."""
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
        """Test getting message history successfully."""
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
        """Test getting message history without authentication."""
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
        """Test starting conversation successfully."""
        conversation_data = {
            "name": "Test Conversation",
            "description": "This is a test conversation",
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
    """Message data validation tests."""

    def test_send_empty_message(
        self,
        client: FlaskClient,
        auth_headers: dict[str, str],
        test_room: str
    ):
        """Test sending empty message."""
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
        """Test sending too long message."""
        # Create message over 10000 characters
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
