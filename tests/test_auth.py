import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.user import User
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def test_user(db: Session):
    user = User(
        email="test@example.com",
        full_name="Test User",
        role="user",
        is_active=True
    )
    user.set_password("testpassword123")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def test_login_success(client, test_user):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "token_type" in response.json()

def test_login_wrong_password(client, test_user):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401

def test_login_inactive_user(client, test_user, db: Session):
    test_user.is_active = False
    db.commit()
    
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )
    assert response.status_code == 401

def test_register_user_by_admin(client):
    # 创建管理员token
    admin_token = create_access_token({"sub": "admin@example.com", "role": "admin"})
    
    response = client.post(
        "/api/v1/auth/register",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "email": "newuser@example.com",
            "password": "newpassword123",
            "full_name": "New User",
            "role": "user"
        }
    )
    assert response.status_code == 201
    assert response.json()["email"] == "newuser@example.com"

def test_register_user_by_non_admin(client):
    # 创建普通用户token
    user_token = create_access_token({"sub": "user@example.com", "role": "user"})
    
    response = client.post(
        "/api/v1/auth/register",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "email": "newuser@example.com",
            "password": "newpassword123",
            "full_name": "New User",
            "role": "user"
        }
    )
    assert response.status_code == 403

def test_password_reset_request(client, test_user):
    response = client.post(
        "/api/v1/auth/password-reset-request",
        json={
            "email": "test@example.com"
        }
    )
    assert response.status_code == 200

def test_password_reset(client, test_user):
    # 模拟重置token
    reset_token = create_access_token({"sub": test_user.email, "type": "reset"})
    
    response = client.post(
        "/api/v1/auth/password-reset",
        json={
            "token": reset_token,
            "new_password": "newpassword123"
        }
    )
    assert response.status_code == 200