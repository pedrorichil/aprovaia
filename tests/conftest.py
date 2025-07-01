import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator
from uuid import uuid4

from main import app
from app.database import Base, get_db
from app.models import Tenant, User, Profile, Question, UserRole
from app.security import get_password_hash

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    connection = engine.connect()
    transaction = connection.begin()
    db = TestingSessionLocal(bind=connection)
    yield db
    db.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def test_client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    del app.dependency_overrides[get_db]

@pytest.fixture(scope="function")
def test_tenant(db_session: Session) -> Tenant:
    tenant = Tenant(name="Tenant de Teste")
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant

@pytest.fixture(scope="function")
def student_user(db_session: Session, test_tenant: Tenant) -> User:
    user = User(id=uuid4(), email="aluno@exemplo.com", password_hash=get_password_hash("senha123"), role=UserRole.student, tenant_id=test_tenant.id)
    db_session.add(user)
    db_session.commit()
    profile = Profile(id=uuid4(), full_name="Aluno de Teste", user_id=user.id)
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def admin_user(db_session: Session, test_tenant: Tenant) -> User:
    user = User(id=uuid4(), email="admin@exemplo.com", password_hash=get_password_hash("admin123"), role=UserRole.admin, tenant_id=test_tenant.id)
    db_session.add(user)
    db_session.commit()
    profile = Profile(id=uuid4(), full_name="Admin de Teste", user_id=user.id)
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def student_auth_token(test_client: TestClient, student_user: User) -> str:
    response = test_client.post(
        "/auth/login",
        data={"username": student_user.email, "password": "senha123"}
    )
    assert response.status_code == 200, f"Login falhou com status {response.status_code} e corpo {response.text}"
    return response.json()["access_token"]

@pytest.fixture(scope="function")
def admin_auth_token(test_client: TestClient, admin_user: User) -> str:
    response = test_client.post(
        "/auth/login",
        data={"username": admin_user.email, "password": "admin123"}
    )
    assert response.status_code == 200, f"Login falhou com status {response.status_code} e corpo {response.text}"
    return response.json()["access_token"]

