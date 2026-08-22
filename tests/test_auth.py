from datetime import UTC, datetime, timedelta

import pytest
from fastapi import status
from sqlalchemy import update

from app.core.exceptions import InvalidTokenError
from app.db.models.auth import Auth
from app.services.auth import AuthService


def test_login_returns_token(client, create_patient):
    patient = create_patient()
    response = client.post("/auth/login", json={"user_id": patient["id"]})
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["user_id"] == patient["id"]
    assert isinstance(body["token"], str) and len(body["token"]) >= 32


def test_login_unknown_user(client):
    response = client.post("/auth/login", json={"user_id": 999999})
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_second_login_rotates_token(client, db_session, create_patient):
    patient = create_patient()
    first = client.post("/auth/login", json={"user_id": patient["id"]}).json()["token"]
    second = client.post("/auth/login", json={"user_id": patient["id"]}).json()["token"]

    assert first != second

    service = AuthService(db_session)
    with pytest.raises(InvalidTokenError):
        service.verify(first)
    assert service.verify(second).token == second


def test_expired_token_rejected_on_protected_route(client, db_session, create_patient, create_booking):
    booking = create_booking()
    token = client.post("/auth/login", json={"user_id": booking["patient_id"]}).json()["token"]

    db_session.execute(
        update(Auth)
        .where(Auth.user_id == booking["patient_id"])
        .values(updated_at=datetime.now(UTC) - timedelta(minutes=31))
    )
    db_session.commit()

    response = client.get(f"/bookings/{booking['id']}/messages?token={token}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
