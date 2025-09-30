import pytest
from fastapi.testclient import TestClient
from fastapi import status


def test_get_balance_without_auth(client: TestClient):
    # Получение баланса без авторизации
    response = client.get("/api/balance")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_balance_with_auth(auth_client: TestClient):
    # Получение баланса с авторизацией
    response = auth_client.get("/api/balance")
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

def test_deposit_balance_success(auth_client: TestClient):
    # Успешное пополнение баланса
    deposit_data = {
        "amount": 100.0
    }

    response = auth_client.post("/api/balance/deposit", json=deposit_data)
    assert response.status_code == status.HTTP_200_OK
    assert "balance" in response.json()


def test_deposit_balance_zero_amount(auth_client: TestClient):
    # Пополнение нулевой суммы
    deposit_data = {
        "amount": 0.0
    }

    response = auth_client.post("/api/balance/deposit", json=deposit_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_withdraw_balance_success(auth_client: TestClient):
    # Сначала пополняем
    auth_client.post("/api/balance/deposit", json={"amount": 100.0})

    # Потом снимаем
    withdraw_data = {
        "amount": 50.0
    }

    response = auth_client.post("/api/balance/withdraw", json=withdraw_data)
    assert response.status_code == status.HTTP_200_OK
    assert "balance" in response.json()


def test_withdraw_balance_insufficient_funds(auth_client: TestClient):
    # Недостаток средств
    withdraw_data = {
        "amount": 100.0
    }

    response = auth_client.post("/api/balance/withdraw", json=withdraw_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_get_transaction_history(auth_client: TestClient):
    # Несколько операций
    auth_client.post("/api/balance/deposit", json={"amount": 100.0})
    auth_client.post("/api/balance/withdraw", json={"amount": 30.0})

    response = auth_client.get("/api/balance/history")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)
    assert len(response.json()) == 2


def test_get_empty_transaction_history(auth_client: TestClient):
    # Пустая история транзакций
    response = auth_client.get("/api/balance/history")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []
