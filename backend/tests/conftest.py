"""Test configuration and shared fixtures."""

import os
import secrets
from typing import Any, Dict, Generator
from uuid import uuid4

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app import create_app
from app.auth import create_tokens, hash_password
from app.database import db
from app.models.user import User, UserEntity, UserRole, UserStatus


class TestConfig:
    """Centralized test configuration."""
    
    # Database configuration from environment or defaults
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres") 
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "ai_chatrooms")
    
    # Test database URL - use environment variable if available
    TEST_DATABASE_URL = os.getenv(
        "DATABASE_URL",
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}_test"
    )
    
    # Base database connection for creating/dropping test databases
    BASE_DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/postgres"
    
    @classmethod
    def get_test_db_name(cls, test_name: str = None) -> str:
        """Generate unique test database name."""
        base_name = f"{cls.POSTGRES_DB}_test"
        if test_name:
            # Create unique DB name for each test module
            return f"{base_name}_{test_name}"
        return base_name
    
    @classmethod
    def get_test_app_config(cls, test_db_name: str = None) -> Dict[str, Any]:
        """Get test application configuration."""
        db_name = test_db_name or cls.get_test_db_name()
        test_db_url = f"postgresql://{cls.POSTGRES_USER}:{cls.POSTGRES_PASSWORD}@{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{db_name}"
        
        return {
            "TESTING": True,
            "DATABASE_URL": test_db_url,
            "JWT_SECRET_KEY": "test-secret-key-" + secrets.token_hex(8),
            "SECRET_KEY": "test-secret-key-" + secrets.token_hex(8),
            "QWEN_API_KEY": "test-api-key",  # Mock API key for tests
            "REDIS_URL": "redis://localhost:6379/1",  # Use different DB for tests
        }


def create_test_database(db_name: str) -> bool:
    """Create test database, return True if successful."""
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        
        conn = psycopg2.connect(TestConfig.BASE_DATABASE_URL)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Drop if exists and create new
        cursor.execute(f"DROP DATABASE IF EXISTS {db_name}")
        cursor.execute(f"CREATE DATABASE {db_name}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Failed to create test database {db_name}: {e}")
        return False


def drop_test_database(db_name: str) -> None:
    """Clean up test database."""
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        
        conn = psycopg2.connect(TestConfig.BASE_DATABASE_URL)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        cursor.execute(f"DROP DATABASE IF EXISTS {db_name}")
        cursor.close()
        conn.close()
        
    except Exception:
        pass  # Ignore cleanup errors


@pytest.fixture(scope="function")
def app() -> Generator[Flask, None, None]:
    """Create test application with isolated database."""
    # Generate unique DB name for this test
    test_db_name = TestConfig.get_test_db_name(f"func_{secrets.token_hex(4)}")
    
    # Create test database
    if not create_test_database(test_db_name):
        pytest.skip("PostgreSQL server not available")
    
    # Create app with test configuration
    app = create_app(TestConfig.get_test_app_config(test_db_name))
    
    with app.app_context():
        # Create all database tables
        from app.models.base import Base
        Base.metadata.create_all(db.engine)
        
        yield app
        
        # Cleanup
        try:
            db.session.close()
            db.engine.dispose()
        except Exception:
            pass
        
        # Drop test database
        drop_test_database(test_db_name)


@pytest.fixture(scope="function")
def client(app: Flask) -> FlaskClient:
    """Create test client."""
    return app.test_client()


@pytest.fixture(scope="function")
def test_user(app: Flask) -> User:
    """Create test user."""
    with app.app_context():
        # Check if user already exists
        existing_user = db.session.query(User).filter_by(username="testuser").first()
        if existing_user:
            return existing_user
        
        # Create new test user
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
        db.session.commit()
        return user


@pytest.fixture(scope="function")
def auth_headers(app: Flask, test_user: User) -> Dict[str, str]:
    """Create authentication headers."""
    with app.app_context():
        # Ensure user is attached to current session
        user = db.session.merge(test_user)
        db.session.refresh(user)
        user_entity = UserEntity.from_model(user)
        tokens = create_tokens(user_entity)
        return {"Authorization": f"Bearer {tokens['access_token']}"}


# Session-scoped fixtures for tests that need to share data
@pytest.fixture(scope="session")
def shared_test_db_name() -> str:
    """Shared test database name for session-scoped tests."""
    return TestConfig.get_test_db_name("session")


@pytest.fixture(scope="session")
def shared_app(shared_test_db_name: str) -> Generator[Flask, None, None]:
    """Session-scoped app for tests that need to share data."""
    # Create test database
    if not create_test_database(shared_test_db_name):
        pytest.skip("PostgreSQL server not available")
    
    # Create app
    app = create_app(TestConfig.get_test_app_config(shared_test_db_name))
    
    with app.app_context():
        from app.models.base import Base
        Base.metadata.create_all(db.engine)
        
        yield app
        
        # Cleanup
        try:
            db.session.close()
            db.engine.dispose()
        except Exception:
            pass
        
        drop_test_database(shared_test_db_name)