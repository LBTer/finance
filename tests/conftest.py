import os
import pytest
from typing import Generator, Any
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.config import settings
from app.db.base import Base
from app.api.deps import get_db


# 使用SQLite内存数据库进行测试
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def db_engine():
    """创建测试数据库引擎"""
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db(db_engine: Any) -> Generator[Session, Any, None]:
    """
    为每个测试函数提供一个独立的数据库会话
    
    每个测试运行在独立的事务中，测试结束后回滚
    """
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()

@pytest.fixture(scope="function")
def client(db: Session) -> Generator:
    """
    创建测试客户端
    
    覆盖依赖注入，使用测试数据库会话
    """
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture(autouse=True)
def test_env():
    """
    设置测试环境变量
    """
    os.environ["TESTING"] = "True"
    os.environ["SECRET_KEY"] = "test_secret_key"
    os.environ["ALGORITHM"] = "HS256"
    os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
    yield
    os.environ.pop("TESTING", None)
    os.environ.pop("SECRET_KEY", None)
    os.environ.pop("ALGORITHM", None)
    os.environ.pop("ACCESS_TOKEN_EXPIRE_MINUTES", None)

@pytest.fixture
def test_password() -> str:
    """测试用密码"""
    return "testpassword123"

@pytest.fixture
def test_email() -> str:
    """测试用邮箱"""
    return "test@example.com"

@pytest.fixture
def test_full_name() -> str:
    """测试用全名"""
    return "Test User"

@pytest.fixture
def test_order_number() -> str:
    """测试用订单号"""
    return "SR202403170001"

@pytest.fixture
def test_product_name() -> str:
    """测试用产品名称"""
    return "Test Product"

@pytest.fixture
def test_headers(client: TestClient, test_user, test_password):
    """
    生成测试用认证头
    """
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user.email,
            "password": test_password,
        },
    )
    tokens = response.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"} 