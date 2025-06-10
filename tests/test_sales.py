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
def test_user(db: Session):
    user = User(
        email="sales@example.com",
        full_name="Sales User",
        role="user",
        is_active=True
    )
    user.set_password("testpassword123")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def test_sales_record(db: Session, test_user):
    record = SalesRecord(
        order_number="SR202403170001",
        user_id=test_user.id,
        product_name="Test Product",
        quantity=1,
        unit_price=100.00,
        total_price=100.00,
        domestic_shipping_fee=10.00,
        overseas_shipping_fee=0.00,
        status="pending",
        remarks="Test record"
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

def test_create_sales_record(client, test_user):
    token = create_access_token({"sub": test_user.email, "role": "user"})
    
    response = client.post(
        "/api/v1/sales",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "order_number": "SR202403170002",
            "product_name": "New Product",
            "quantity": 2,
            "unit_price": 150.00,
            "total_price": 300.00,
            "domestic_shipping_fee": 15.00,
            "overseas_shipping_fee": 0.00,
            "status": "pending",
            "remarks": "New test record"
        }
    )
    assert response.status_code == 201
    assert response.json()["product_name"] == "New Product"

def test_get_sales_records_list(client, test_user, test_sales_record):
    token = create_access_token({"sub": test_user.email, "role": "user"})
    
    response = client.get(
        "/api/v1/sales",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert len(response.json()["items"]) > 0

def test_get_sales_record_detail(client, test_user, test_sales_record):
    token = create_access_token({"sub": test_user.email, "role": "user"})
    
    response = client.get(
        f"/api/v1/sales/{test_sales_record.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["order_number"] == "SR202403170001"

def test_update_sales_record(client, test_user, test_sales_record):
    token = create_access_token({"sub": test_user.email, "role": "user"})
    
    response = client.put(
        f"/api/v1/sales/{test_sales_record.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "quantity": 3,
            "remarks": "Updated test record"
        }
    )
    assert response.status_code == 200
    assert response.json()["quantity"] == 3
    assert response.json()["remarks"] == "Updated test record"

def test_delete_sales_record(client, test_user, test_sales_record):
    token = create_access_token({"sub": test_user.email, "role": "user"})
    
    response = client.delete(
        f"/api/v1/sales/{test_sales_record.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 204

def test_access_other_user_record(client, test_user, test_sales_record, db: Session):
    # 创建另一个用户
    other_user = User(
        email="other@example.com",
        full_name="Other User",
        role="user",
        is_active=True
    )
    other_user.set_password("testpassword123")
    db.add(other_user)
    db.commit()
    
    token = create_access_token({"sub": other_user.email, "role": "user"})
    
    response = client.get(
        f"/api/v1/sales/{test_sales_record.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403 