import database, test, services, modelses
from modelses.user import User
from modelses.event import Event
from modelses.balance import Balance
from modelses.transaction import Trans
from modelses.models import PredictionResult

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from test.api1.api import app
from database.databases import get_session, engine
from services.auth.jwt_handler import create_access_token
from services.auth.authenticate import get_password_hash, get_current_user

SQLModel.metadata.create_all(bind=engine)

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///testing.db",
                           connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    # app.dependency_overrides[authenticate] = lambda: "user@test.ru"
    async def mock_get_current_user():
        return {"user_id": 1, "username": "testuser", "email": "test@test.ru"}

    app.dependency_overrides[get_current_user] = mock_get_current_user

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

@pytest.fixture(name="auth_client")
def auth_client_fixture(client: TestClient, session: Session):
    # Создаем тестового пользователя напрямую в БД
    from modelses.user import User
    from services.auth.authenticate import get_password_hash

    # Создаем пользователя
    test_user = User(
        username="testuser",
        email="test@test.ru",
        password_hash=get_password_hash("Test1234")
    )
    session.add(test_user)
    session.commit()
    session.refresh(test_user)

    # Создаем токен
    token = create_access_token(test_user.user_id, test_user.username)

    # Создаем авторизованный клиент
    auth_client = TestClient(app)
    auth_client.headers.update({"Authorization": f"Bearer {token}"})

    return auth_client


@pytest.fixture(name="test_user")
def test_user_fixture(session: Session):
    from modelses.user import User
    from services.auth.authenticate import get_password_hash

    user = User(
        username="fixtureuser",
        email="fixture@test.ru",
        password_hash=get_password_hash("Fixture123")
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user