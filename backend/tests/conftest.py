import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base
from app.dependencies import get_db
from app.auth.passwords import hash_password
from app.models.user import User

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_guardai.db"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Create admin, manager, user test accounts
    admin = User(
        username="test_admin",
        email="test_admin@example.com",
        password_hash=hash_password("adminpass123"),
        role="ADMIN",
        is_active=True,
    )
    manager = User(
        username="test_manager",
        email="test_manager@example.com",
        password_hash=hash_password("managerpass123"),
        role="MANAGER",
        is_active=True,
    )
    user = User(
        username="test_user",
        email="test_user@example.com",
        password_hash=hash_password("userpass123"),
        role="EMPLOYEE",
        is_active=True,
    )
    db.add_all([admin, manager, user])
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def admin_token(client):
    res = client.post("/auth/login", data={"username": "test_admin", "password": "adminpass123"})
    return res.json()["access_token"]


@pytest.fixture
def user_token(client):
    res = client.post("/auth/login", data={"username": "test_user", "password": "userpass123"})
    return res.json()["access_token"]


@pytest.fixture
def manager_token(client):
    res = client.post("/auth/login", data={"username": "test_manager", "password": "managerpass123"})
    return res.json()["access_token"]
