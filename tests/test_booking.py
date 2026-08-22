from datetime import datetime, timedelta

import pytest
from fastapi import WebSocketDisconnect, status
from sqlalchemy import select

from app.db.models.chat_room import ChatRoom
from app.db.models.message import Message


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


# --- History Endpoint Tests ---


def test_history_requires_token(client, create_booking):
    booking = create_booking()
    response = client.get(f"/bookings/{booking['id']}/messages")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_history_invalid_token(client, create_booking):
    booking = create_booking()
    response = client.get(f"/bookings/{booking['id']}/messages?token=bogus")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_history_non_participant_denied(client, login_token, create_booking, create_patient):
    booking = create_booking()
    outsider = create_patient()
    response = client.get(f"/bookings/{booking['id']}/messages?token={login_token(outsider['id'])}")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_history_before_first_ws_connection(client, login_token, create_booking):
    booking = create_booking()
    token = login_token(booking["patient_id"])
    response = client.get(f"/bookings/{booking['id']}/messages?token={token}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_history_cancelled_booking_denied(client, login_token, create_booking):
    booking = create_booking()
    cancel = client.patch(f"/bookings/cancel?booking_id={booking['id']}")
    assert cancel.status_code == status.HTTP_200_OK
    token = login_token(booking["patient_id"])
    response = client.get(f"/bookings/{booking['id']}/messages?token={token}")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_history_newest_first_with_schema(client, login_token, create_booking):
    booking = create_booking()
    token = login_token(booking["patient_id"])
    with client.websocket_connect(f"/bookings/{booking['id']}/ws?token={token}") as ws:
        ws.send_text("first")
        ws.send_text("second")

    response = client.get(f"/bookings/{booking['id']}/messages?token={token}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    contents = [m["content"] for m in data]
    assert "first" in contents and "second" in contents
    assert contents.index("second") < contents.index("first")
    for item in data:
        assert set(item.keys()) == {"sender_id", "room_id", "type", "content", "id", "updated_at"}
        assert item["type"] == "text"


# --- WebSocket Chat Tests ---


def _make_chat_party(client, db_session, login_token, create_patient, create_doctor, create_slot):
    patient = create_patient()
    doctor = create_doctor()
    slot = create_slot(doctor_id=doctor["id"])
    resp = client.post("/bookings/", json={"patient_id": patient["id"], "slot_id": slot["id"]})
    assert resp.status_code == status.HTTP_201_CREATED
    booking = resp.json()
    return patient, doctor, booking, login_token(patient["id"]), login_token(doctor["id"])


def test_chat_auth_failure(client):
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/bookings/1/ws?token=invalid_token"):
            pass


def test_chat_booking_not_found(client, login_token, create_patient):
    patient = create_patient()
    token = login_token(patient["id"])
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(f"/bookings/9999/ws?token={token}"):
            pass


def test_chat_unauthorized_user(client, login_token, create_booking, create_patient):
    booking = create_booking()
    outsider = create_patient()
    token = login_token(outsider["id"])
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(f"/bookings/{booking['id']}/ws?token={token}"):
            pass


def test_chat_invalid_booking_status(client, login_token, create_booking):
    booking = create_booking()
    cancel = client.patch(f"/bookings/cancel?booking_id={booking['id']}")
    assert cancel.status_code == status.HTTP_200_OK
    token = login_token(booking["patient_id"])
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(f"/bookings/{booking['id']}/ws?token={token}"):
            pass


def test_chat_two_party_delivery_and_persistence(
    client, db_session, login_token, create_patient, create_doctor, create_slot
):
    patient, doctor, booking, ptok, dtok = _make_chat_party(
        client, db_session, login_token, create_patient, create_doctor, create_slot
    )

    with client.websocket_connect(f"/bookings/{booking['id']}/ws?token={ptok}") as pws:
        with client.websocket_connect(f"/bookings/{booking['id']}/ws?token={dtok}") as dws:
            pws.send_text("hello doc")
            got = dws.receive_json()
            assert got == {"sender_id": patient["id"], "type": "message", "message": "hello doc"}

            dws.send_text("hi patient")
            presence = pws.receive_json()
            assert presence == {"sender_id": doctor["id"], "type": "behaviour", "behaviour": "presence"}
            reply = pws.receive_json()
            assert reply == {"sender_id": doctor["id"], "type": "message", "message": "hi patient"}

    room = db_session.scalars(select(ChatRoom).where(ChatRoom.booking_id == booking["id"])).first()
    assert room is not None
    saved = db_session.scalars(
        select(Message).where(Message.room_id == room.id).order_by(Message.created_at, Message.id)
    ).all()
    assert [(m.sender_id, m.content) for m in saved] == [
        (patient["id"], "hello doc"),
        (doctor["id"], "hi patient"),
    ]


def test_chat_rejection_flow(client, db_session, login_token, create_patient, create_doctor, create_slot):
    patient, doctor, booking, ptok, dtok = _make_chat_party(
        client, db_session, login_token, create_patient, create_doctor, create_slot
    )
    oversized = "x" * 300

    with client.websocket_connect(f"/bookings/{booking['id']}/ws?token={ptok}") as pws:
        with client.websocket_connect(f"/bookings/{booking['id']}/ws?token={dtok}") as dws:
            pws.send_text(oversized)
            presence = pws.receive_json()
            assert presence == {"sender_id": doctor["id"], "type": "behaviour", "behaviour": "presence"}

            err = pws.receive_json()
            assert err == {
                "sender_id": patient["id"],
                "type": "error",
                "code": "message_too_long",
                "limit": 256,
                "received_length": 300,
            }

            pws.send_text("after rejection")
            frame = dws.receive_json()
            assert frame == {"sender_id": patient["id"], "type": "message", "message": "after rejection"}

    room = db_session.scalars(select(ChatRoom).where(ChatRoom.booking_id == booking["id"])).first()
    saved = db_session.scalars(select(Message).where(Message.room_id == room.id)).all()
    assert [m.content for m in saved] == ["after rejection"]
    assert oversized not in [m.content for m in saved]


