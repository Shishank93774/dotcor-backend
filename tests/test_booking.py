from datetime import datetime, timedelta

from fastapi import status


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
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


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

