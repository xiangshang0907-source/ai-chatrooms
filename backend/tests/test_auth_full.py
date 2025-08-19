"""完整的PostgreSQL认证功能测试."""

import json
import uuid

import pytest

from app import create_app
from app.auth import hash_password
from app.database import db
from tests.test_models import SimpleUser


@pytest.fixture
def app():
    """创建测试应用."""
    # 使用唯一的测试数据库名
    test_db_name = f"ai_chatrooms_test_{uuid.uuid4().hex[:8]}"
    
    app = create_app({
        "TESTING": True,
        "DATABASE_URL": f"postgresql://postgres:postgres@localhost:5432/{test_db_name}",
        "JWT_SECRET_KEY": "test-secret-key",
    })
    
    # 创建测试数据库
    import psycopg2
    conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5432/postgres')
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(f'CREATE DATABASE "{test_db_name}"')
    cur.close()
    conn.close()
    
    with app.app_context():
        # 只创建测试用户表
        SimpleUser.__table__.create(db.engine)
        yield app
        
        # 清理
        db.session.close()
        db.engine.dispose()
        
    # 删除测试数据库
    conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5432/postgres')
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(f'DROP DATABASE IF EXISTS "{test_db_name}"')
    cur.close()
    conn.close()


@pytest.fixture
def client(app):
    """创建测试客户端."""
    return app.test_client()


class TestPostgreSQLConnection:
    """PostgreSQL连接测试."""

    def test_database_connection(self, app):
        """测试数据库连接."""
        with app.app_context():
            # 测试能否执行SQL查询
            result = db.session.execute(db.text("SELECT 1 as test")).fetchone()
            assert result[0] == 1

    def test_create_user_record(self, app):
        """测试创建用户记录."""
        with app.app_context():
            user = SimpleUser(
                username="testuser",
                email="test@example.com",
                password_hash=hash_password("password123"),
                display_name="Test User"
            )
            db.session.add(user)
            db.session.commit()
            
            # 验证用户已创建
            found_user = db.session.query(SimpleUser).filter_by(username="testuser").first()
            assert found_user is not None
            assert found_user.email == "test@example.com"
            assert found_user.display_name == "Test User"

    def test_api_endpoints_basic(self, client):
        """测试基础API端点."""
        # 测试健康检查
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.get_json()
        assert data["status"] == "ok"

    def test_api_validation(self, client):
        """测试API数据验证."""
        # 测试无效注册数据
        invalid_data = {
            "username": "ab",  # 太短
            "email": "invalid-email",  # 无效邮箱
            "password": "123"  # 太短
        }
        
        response = client.post(
            "/auth/register",
            data=json.dumps(invalid_data),
            content_type="application/json"
        )
        
        assert response.status_code == 400
        response_data = response.get_json()
        assert response_data["error"] == "validation_error"
