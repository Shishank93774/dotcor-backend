from datetime import datetime, timedelta

import pytest
from fastapi import WebSocketDisconnect, status


def test_create_booking(client, create_patient, create_slot):
    patient = create_patient()
    slot = create_slot()
    payload = {"patient_id": patient["id"], "slot_id": slot["id"]}
    response = client.post("/bookings/", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["patient_id"] == patient["id"]
    assert data["slot_id"] == slot["id"]
    assert data["status"] == "booked"
    assert "id" in data


def test_create_booking_slot_already_booked(client, create_patient, create_slot):
    patient1 = create_patient(username="pat1")
    patient2 = create_patient(username="pat2")
    slot = create_slot()
    # First booking
    client.post("/bookings/", json={"patient_id": patient1["id"], "slot_id": slot["id"]})
    # Second booking same slot
    response = client.post("/bookings/", json={"patient_id": patient2["id"], "slot_id": slot["id"]})
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] == "Slot already booked"


def test_get_booking(client, create_patient, create_slot):
    patient = create_patient()
    slot = create_slot()
    # Create via endpoint to have full data
    resp = client.post("/bookings/", json={"patient_id": patient["id"], "slot_id": slot["id"]})
    booking_id = resp.json()["id"]
    response = client.get(f"/bookings/{booking_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == booking_id


def test_list_bookings(client, create_patient, create_slot):
    patient = create_patient()
    slot1 = create_slot(start_time=datetime.now() + timedelta(days=4))
    slot2 = create_slot(start_time=datetime.now() + timedelta(days=5))
    client.post("/bookings/", json={"patient_id": patient["id"], "slot_id": slot1["id"]})
    client.post("/bookings/", json={"patient_id": patient["id"], "slot_id": slot2["id"]})
    response = client.get("/bookings/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) >= 2
    # You can check if both appear (may contain others, but at least these)
    slot_ids = [b["slot_id"] for b in data]
    assert slot1["id"] in slot_ids
    assert slot2["id"] in slot_ids


def test_cancel_booking(client, create_patient, create_slot):
    patient = create_patient()
    slot = create_slot()
    resp = client.post("/bookings/", json={"patient_id": patient["id"], "slot_id": slot["id"]})
    booking_id = resp.json()["id"]
    # Cancel using PATCH /bookings/cancel?booking_id=...
    response = client.patch(f"/bookings/cancel?booking_id={booking_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "cancelled"
    # Verify get booking returns cancelled
    get_resp = client.get(f"/bookings/{booking_id}")
    assert get_resp.json()["status"] == "cancelled"


def test_cancel_booking_not_found(client):
    response = client.patch("/bookings/cancel?booking_id=9999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_create_booking_invalid_patient(client, create_slot):
    slot = create_slot()
    payload = {"patient_id": 9999, "slot_id": slot["id"]}
    response = client.post("/bookings/", json=payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Patient not found"


def test_create_booking_invalid_slot(client, create_patient):
    patient = create_patient()
    payload = {"patient_id": patient["id"], "slot_id": 9999}
    response = client.post("/bookings/", json=payload)
    # The BookingService.create_booking uses a try-except IntegrityError
    # for invalid patient/slot IDs.
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_cancel_booking_already_cancelled(client, create_patient, create_slot):
    patient = create_patient()
    slot = create_slot()
    resp = client.post("/bookings/", json={"patient_id": patient["id"], "slot_id": slot["id"]})
    booking_id = resp.json()["id"]

    # First cancellation
    client.patch(f"/bookings/cancel?booking_id={booking_id}")
    # Second cancellation
    response = client.patch(f"/bookings/cancel?booking_id={booking_id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "cancelled"


def test_booking_lifecycle_rebook(client, create_patient, create_slot):
    # 1. Setup patients and slot
    pat1 = create_patient(username="pat1")
    pat2 = create_patient(username="pat2")
    slot = create_slot()

    # 2. Pat1 books the slot
    resp1 = client.post("/bookings/", json={"patient_id": pat1["id"], "slot_id": slot["id"]})
    assert resp1.status_code == status.HTTP_201_CREATED
    booking_id = resp1.json()["id"]

    # 3. Pat2 tries to book the same slot (should fail)
    resp2_fail = client.post("/bookings/", json={"patient_id": pat2["id"], "slot_id": slot["id"]})
    assert resp2_fail.status_code == status.HTTP_409_CONFLICT
    assert resp2_fail.json()["detail"] == "Slot already booked"

    # 4. Pat1 cancels the booking
    cancel_resp = client.patch(f"/bookings/cancel?booking_id={booking_id}")
    assert cancel_resp.status_code == status.HTTP_200_OK
    assert cancel_resp.json()["status"] == "cancelled"

    # 5. Pat2 tries to book the slot again (should succeed now)
    resp2_success = client.post("/bookings/", json={"patient_id": pat2["id"], "slot_id": slot["id"]})
    assert resp2_success.status_code == status.HTTP_201_CREATED
    data2 = resp2_success.json()
    assert data2["patient_id"] == pat2["id"]
    assert data2["slot_id"] == slot["id"]
    assert data2["status"] == "booked"


def test_delete_booking(client, create_patient, create_slot):
    patient = create_patient()
    slot = create_slot()
    resp = client.post("/bookings/", json={"patient_id": patient["id"], "slot_id": slot["id"]})
    booking_id = resp.json()["id"]

    # Delete booking
    response = client.delete(f"/bookings/{booking_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify deletion
    get_resp = client.get(f"/bookings/{booking_id}")
    assert get_resp.status_code == status.HTTP_404_NOT_FOUND


def test_delete_booking_not_found(client):
    response = client.delete("/bookings/9999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


# --- WebSocket Tests ---


def get_token(db_session, user_id):
    from app.services.auth import AuthService

    auth_service = AuthService(db_session)
    return auth_service.login(user_id).token


def test_chat_auth_failure(client):
    # Attempt to connect with an invalid token
    # FastAPI's TestClient raises WebSocketException as a standard exception during connect
    with pytest.raises(Exception):
        with client.websocket_connect("/bookings/1/ws?token=invalid_token"):
            pass


def test_chat_booking_not_found(client, db_session, create_patient):
    patient = create_patient()
    token = get_token(db_session, patient["id"])
    with pytest.raises(Exception):
        with client.websocket_connect(f"/bookings/9999/ws?token={token}"):
            pass


def test_chat_invalid_booking_status(client, db_session, create_patient, create_slot):
    patient = create_patient()
    slot = create_slot()
    resp = client.post("/bookings/", json={"patient_id": patient["id"], "slot_id": slot["id"]})
    booking_id = resp.json()["id"]
    client.patch(f"/bookings/cancel?booking_id={booking_id}")

    token = get_token(db_session, patient["id"])
    with pytest.raises(Exception):
        with client.websocket_connect(f"/bookings/{booking_id}/ws?token={token}"):
            pass


def test_chat_unauthorized_user(client, db_session, create_patient, create_slot):
    patient1 = create_patient()
    patient2 = create_patient()
    slot = create_slot()
    resp = client.post("/bookings/", json={"patient_id": patient1["id"], "slot_id": slot["id"]})
    booking_id = resp.json()["id"]

    token2 = get_token(db_session, patient2["id"])
    with pytest.raises(Exception):
        with client.websocket_connect(f"/bookings/{booking_id}/ws?token={token2}"):
            pass


def test_chat_success_and_message_save(client, db_session, create_patient, create_slot, create_doctor):
    patient = create_patient()
    doctor = create_doctor()
    slot = create_slot(doctor_id=doctor["id"])
    resp = client.post("/bookings/", json={"patient_id": patient["id"], "slot_id": slot["id"]})
    booking_id = resp.json()["id"]

    token = get_token(db_session, patient["id"])
    with client.websocket_connect(f"/bookings/{booking_id}/ws?token={token}") as websocket:
        msg = "Hello Doctor!"
        websocket.send_text(msg)
        data = websocket.receive_json()
        assert data["message"] == msg
        assert data["sender"] == patient["id"]

    from app.db.models.message import Message
    from sqlalchemy import select

    stmt = select(Message).where(Message.room_id == booking_id, Message.content == msg)
    message = db_session.scalars(stmt).first()
    assert message is not None
    assert message.sender_id == patient["id"]


def test_chat_message_too_long(client, db_session, create_patient, create_slot):
    patient = create_patient()
    slot = create_slot()
    resp = client.post("/bookings/", json={"patient_id": patient["id"], "slot_id": slot["id"]})
    booking_id = resp.json()["id"]

    token = get_token(db_session, patient["id"])
    with client.websocket_connect(f"/bookings/{booking_id}/ws?token={token}") as websocket:
        long_msg = "a" * 257
        websocket.send_text(long_msg)
        # The server should raise a WebSocketException and close the connection
        with pytest.raises(WebSocketDisconnect):
            websocket.receive_text()
