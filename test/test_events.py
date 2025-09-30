import pytest
from fastapi.testclient import TestClient
from fastapi import status
from datetime import date


def test_get_events_without_auth(client: TestClient):
    # Событий без авторизации
    response = client.get("/api/events/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_events_with_auth(auth_client: TestClient):
    # Событий с авторизацией
    response = auth_client.get("/api/events/")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)


def test_create_event_success(auth_client: TestClient):
    # Успешное создание события
    event_data = {
        "description": "Test Event Description",
        "creator_id": 1
    }

    response = auth_client.post("/api/events/new/", json=event_data)
    assert response.status_code == status.HTTP_200_OK
    assert "event_id" in response.json()


def test_create_event_missing_fields(auth_client: TestClient):
    # События с отсутствующими полями
    event_data = {
        "description": "Test Event"  # Нет creator_id
    }

    response = auth_client.post("/api/events/new/", json=event_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_get_specific_event_success(auth_client: TestClient):
    # Создание события
    event_data = {
        "description": "Specific Event",
        "creator_id": 1
    }
    create_response = auth_client.post("/api/events/new/", json=event_data)
    event_id = create_response.json()["event_id"]

    # Получение события
    response = auth_client.get(f"/api/events/{event_id}/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["event_id"] == event_id


def test_get_nonexistent_event(auth_client: TestClient):
    # Несуществующее событие
    response = auth_client.get("/api/events/999/")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_event_success(auth_client: TestClient):
    # Создание события
    event_data = {
        "description": "Event to delete",
        "creator_id": 1
    }
    create_response = auth_client.post("/api/events/new/", json=event_data)
    event_id = create_response.json()["event_id"]

    # Удаление события
    response = auth_client.delete(f"/api/events/{event_id}")
    assert response.status_code == status.HTTP_200_OK


def test_delete_nonexistent_event(auth_client: TestClient):
    # Несуществующее событие
    response = auth_client.delete("/api/events/999/")
    assert response.status_code == status.HTTP_404_NOT_FOUND