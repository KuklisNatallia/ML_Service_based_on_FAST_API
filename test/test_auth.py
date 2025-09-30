import pytest
from fastapi.testclient import TestClient
from fastapi import status


def test_user_registration_success(client: TestClient):
    # Регистрация пользователя
    user_data = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "Test1234"
    }

    response = client.post("/api/users/register", json=user_data)
    assert response.status_code == status.HTTP_200_OK
    assert "user_id" in response.json()
    #assert response.json()["email"] == "newuser@example.com"


def test_user_registration_failure_short_password(client: TestClient):
    # short пароль
    user_data = {
        "username": "testuser",
        "email": "test2@example.com",
        "password": "short"
    }

    response = client.post("/api/users/register", data=user_data)
    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert "error=Пароль должен содержать минимум 8 символов" in response.headers["location"]


def test_user_registration_failure_duplicate_email(client: TestClient):
    # дубликат email
    # Первая регистрация
    user_data = {
        "username": "user1",
        "email": "duplicate@example.com",
        "password": "Test1234"
    }
    client.post("/api/users/register", data=user_data)

    # 2я попытка с тем же email
    user_data2 = {
        "username": "user2",
        "email": "duplicate@example.com",
        "password": "Test1234"
    }

    response = client.post("/api/users/register", data=user_data2)
    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert "error=Пользователь с таким email уже существует" in response.headers["location"]


def test_user_login_success(client: TestClient):
    # Сначала регистрируем
    user_data = {
        "username": "loginuser",
        "email": "login@example.com",
        "password": "Test1234"
    }
    client.post("/api/users/register", json=user_data)

    # Пытаемся залогиниться
    login_data = {
        "username": "login@example.com",
        "password": "Test1234"
    }

    response = client.post("/api/users/login", json=login_data)
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()


def test_user_login_failure_wrong_password(client: TestClient):
    # Сначала регистрируем
    user_data = {
        "username": "loginuser2",
        "email": "login2@example.com",
        "password": "Test1234"
    }
    client.post("/api/users/register", data=user_data)

    # Неверный пароль
    login_data = {
        "username": "login2@example.com",
        "password": "WrongPassword"
    }

    response = client.post("/api/users/login", data=login_data)
    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert "error=Неверный email или пароль" in response.headers["location"]

def test_user_login_failure_nonexistent_email(client: TestClient):
    # Несуществующий email
    login_data = {
        "username": "nonexistent@example.com",
        "password": "Test1234"
    }

    response = client.post("/auth/login", data=login_data)
    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert "error=Неверный email или пароль" in response.headers["location"]


def test_get_current_user_info(auth_client: TestClient):
    # Информация о текущем пользователе
    response = auth_client.get("/api/users/me")
    assert response.status_code == status.HTTP_200_OK
    assert "balance" in response.json()


def test_logout(auth_client: TestClient):
    # Выход из системы
    response = auth_client.post("/logout")
    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert response.headers["location"] == "/?success=Выход выполнен успешно!"