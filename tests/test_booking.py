from datetime import datetime, timedelta

from fastapi import status


def test_create_booking(client, create_patient, create_slot):
    patient = create_patient()
    slot = create_slot()
    payload = {"patient_id": patient.id, "slot_id": slot.id}
    response = client.post("/bookings/", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["patient_id"] == patient.id
    assert data["slot_id"] == slot.id
    assert data["status"] == "booked"
    assert "id" in data


def test_create_booking_slot_already_booked(client, create_patient, create_slot):
    patient1 = create_patient(username="p1")
    patient2 = create_patient(username="p2")
    slot = create_slot()
    # First booking
    client.post("/bookings/", json={"patient_id": patient1.id, "slot_id": slot.id})
    # Second booking same slot
    response = client.post("/bookings/", json={"patient_id": patient2.id, "slot_id": slot.id})
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] == "Slot already booked"


def test_get_booking(client, create_patient, create_slot):
    patient = create_patient()
    slot = create_slot()
    # Create via endpoint to have full data
    resp = client.post("/bookings/", json={"patient_id": patient.id, "slot_id": slot.id})
    booking_id = resp.json()["id"]
    response = client.get(f"/bookings/{booking_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == booking_id


def test_list_bookings(client, create_patient, create_slot):
    patient = create_patient()
    slot1 = create_slot(start_time=datetime.now() + timedelta(days=4))
    slot2 = create_slot(start_time=datetime.now() + timedelta(days=5))
    client.post("/bookings/", json={"patient_id": patient.id, "slot_id": slot1.id})
    client.post("/bookings/", json={"patient_id": patient.id, "slot_id": slot2.id})
    response = client.get("/bookings/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) >= 2
    # You can check if both appear (may contain others, but at least these)
    slot_ids = [b["slot_id"] for b in data]
    assert slot1.id in slot_ids
    assert slot2.id in slot_ids


def test_cancel_booking(client, create_patient, create_slot):
    patient = create_patient()
    slot = create_slot()
    resp = client.post("/bookings/", json={"patient_id": patient.id, "slot_id": slot.id})
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
