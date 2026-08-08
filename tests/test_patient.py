from fastapi import status


def test_create_patient(client):
    payload = {"username": "alice", "email": "alice@example.com", "password": "pass123", "contact_number": "+91 8966352478"}
    response = client.post("/users/patients/", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["username"] == "alice"
    assert data["email"] == "alice@example.com"
    assert "id" in data
    assert "role" in data and data["role"] == "patient"


def test_get_patient(client, create_patient):
    patient = create_patient(username="bob", email="bob@example.com")
    response = client.get(f"/users/patients/{patient['id']}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == patient["id"]
    assert data["username"] == "bob"


def test_get_patients_list(client, create_patient):
    create_patient(username="pat1")
    create_patient(username="pat2")
    response = client.get("/users/patients/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) >= 2
    usernames = [p["username"] for p in data]
    assert "pat1" in usernames
    assert "pat2" in usernames


def test_get_patient_not_found(client):
    response = client.get("/users/patients/9999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Patient not found"


def test_create_patient_duplicate_username(client, create_patient):
    create_patient(username="duplicate", email="dup1@example.com")
    payload = {"username": "duplicate", "email": "dup2@example.com", "password": "pass", "contact_number": "+918966352782"}
    response = client.post("/users/patients/", json=payload)
    assert response.status_code == status.HTTP_409_CONFLICT


def test_create_patient_duplicate_email(client, create_patient):
    create_patient(email="dup@example.com")
    payload = {"username": "new_pat", "email": "dup@example.com", "password": "pass", "contact_number": "+918888888888"}
    response = client.post("/users/patients/", json=payload)
    assert response.status_code == status.HTTP_409_CONFLICT


def test_create_patient_duplicate_contact(client, create_patient):
    create_patient(contact_number="+918888888888")
    payload = {"username": "new_pat", "email": "unique@example.com", "password": "pass", "contact_number": "+918888888888"}
    response = client.post("/users/patients/", json=payload)
    assert response.status_code == status.HTTP_409_CONFLICT


def test_delete_patient(client, create_patient):
    patient = create_patient(username="pat_delete")
    patient_id = patient["id"]

    # Delete patient
    response = client.delete(f"/users/patients/{patient_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify deletion
    get_response = client.get(f"/users/patients/{patient_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_patient_cascades(client, create_doctor, create_slot, create_patient):
    # 1. Setup: Patient -> Booking (with existing slot)
    patient = create_patient(username="pat_cascade")
    patient_id = patient["id"]
    doctor = create_doctor()
    slot = create_slot(doctor_id=doctor["id"])
    slot_id = slot["id"]

    # Create booking
    booking_resp = client.post("/bookings/", json={"patient_id": patient_id, "slot_id": slot_id})
    booking_id = booking_resp.json()["id"]

    # 2. Delete Patient
    response = client.delete(f"/users/patients/{patient_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # 3. Verify Cascade: Booking should be gone
    booking_resp = client.get(f"/bookings/{booking_id}")
    assert booking_resp.status_code == status.HTTP_404_NOT_FOUND

    # 4. Verify Slot still exists (Slot is owned by Doctor, not Patient)
    slot_resp = client.get(f"/slots/{slot_id}")
    assert slot_resp.status_code == status.HTTP_200_OK
