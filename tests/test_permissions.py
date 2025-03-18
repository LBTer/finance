import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.user import User
from app.models.sales_record import SalesRecord
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def admin_user(db: Session):
    user = User(
        email="admin@example.com",
        full_name="Admin User",
        role="admin",
        is_active=True
    )
    user.set_password("adminpass123")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def manager_user(db: Session):
    user = User(
        email="manager@example.com",
        full_name="Manager User",
        role="manager",
        is_active=True
    )
    user.set_password("managerpass123")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def sales_user(db: Session):
    user = User(
        email="sales@example.com",
        full_name="Sales User",
        role="user",
        is_active=True
    )
    user.set_password("salespass123")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def test_record(db: Session, sales_user):
    record = SalesRecord(
        order_number="SR202403170001",
        user_id=sales_user.id,
        product_name="Test Product",
        quantity=1,
        unit_price=100.00,
        shipping_fee=10.00,
        status="pending",
        remarks="Test record"
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

def test_admin_access_all_records(client, admin_user, test_record):
    token = create_access_token({"sub": admin_user.email, "role": "admin"})
    
    response = client.get(
        "/api/v1/sales",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert len(response.json()["items"]) > 0

def test_manager_access_all_records(client, manager_user, test_record):
    token = create_access_token({"sub": manager_user.email, "role": "manager"})
    
    response = client.get(
        "/api/v1/sales",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert len(response.json()["items"]) > 0

def test_sales_access_own_records(client, sales_user, test_record):
    token = create_access_token({"sub": sales_user.email, "role": "user"})
    
    response = client.get(
        "/api/v1/sales",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    records = response.json()["items"]
    assert len(records) > 0
    assert all(record["user_id"] == sales_user.id for record in records)

def test_manager_approve_record(client, manager_user, test_record):
    token = create_access_token({"sub": manager_user.email, "role": "manager"})
    
    response = client.put(
        f"/api/v1/sales/{test_record.id}/approve",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "approved"

def test_sales_cannot_approve_record(client, sales_user, test_record):
    token = create_access_token({"sub": sales_user.email, "role": "user"})
    
    response = client.put(
        f"/api/v1/sales/{test_record.id}/approve",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403

def test_admin_user_management(client, admin_user):
    token = create_access_token({"sub": admin_user.email, "role": "admin"})
    
    # 测试创建新用户
    response = client.post(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "email": "newuser@example.com",
            "password": "newpass123",
            "full_name": "New User",
            "role": "user"
        }
    )
    assert response.status_code == 201
    
    # 测试获取用户列表
    response = client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_non_admin_user_management(client, sales_user):
    token = create_access_token({"sub": sales_user.email, "role": "user"})
    
    # 测试创建新用户（应该被拒绝）
    response = client.post(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "email": "newuser@example.com",
            "password": "newpass123",
            "full_name": "New User",
            "role": "user"
        }
    )
    assert response.status_code == 403
    
    # 测试获取用户列表（应该被拒绝）
    response = client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403