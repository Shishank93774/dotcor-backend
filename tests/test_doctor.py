from fastapi import status


def test_create_doctor(client):
    payload = {
        "username": "dr_strange",
        "email": "strange@marvel.com",
        "password": "mystic",
        "contact_number": "+91 8789923577",
        "specialization": "Neurology",
    }
    response = client.post("/users/doctors/", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["username"] == "dr_strange"
    assert data["specialization"] == "Neurology"
    assert data["role"] == "doctor"


def test_get_doctor(client, create_doctor):
    doctor = create_doctor(username="dr_who")
    response = client.get(f"/users/doctors/{doctor['id']}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == doctor["id"]
    assert data["username"] == "dr_who"


def test_get_doctors_list(client, create_doctor):
    create_doctor(username="doc1")
    create_doctor(username="doc2")
    response = client.get("/users/doctors/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) >= 2
    # public view should not expose email/contact
    assert "email" not in data[0]  # DoctorReadPublic excludes them


def test_create_doctor_duplicate_email(client, create_doctor):
    create_doctor(email="dup@example.com")
    payload = {
        "username": "new_doc",
        "email": "dup@example.com",
        "password": "password",
        "contact_number": "+918888888888",
        "specialization": "Surgery",
    }
    response = client.post("/users/doctors/", json=payload)
    assert response.status_code == status.HTTP_409_CONFLICT


def test_create_doctor_duplicate_contact(client, create_doctor):
    create_doctor(contact_number="+918888888888")
    payload = {
        "username": "new_doc",
        "email": "unique@example.com",
        "password": "password",
        "contact_number": "+918888888888",
        "specialization": "Surgery",
    }
    response = client.post("/users/doctors/", json=payload)
    assert response.status_code == status.HTTP_409_CONFLICT


def test_delete_doctor(client, create_doctor):
    doctor = create_doctor(username="dr_delete")
    doctor_id = doctor["id"]

    # Delete doctor
    response = client.delete(f"/users/doctors/{doctor_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify deletion
    get_response = client.get(f"/users/doctors/{doctor_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_doctor_cascades(client, create_doctor, create_slot, create_patient):
    # 1. Setup: Doctor -> Slot -> Booking
    doctor = create_doctor(username="dr_cascade")
    doctor_id = doctor["id"]
    slot = create_slot(doctor_id=doctor_id)
    slot_id = slot["id"]
    patient = create_patient()

    # Create booking
    booking_resp = client.post("/bookings/", json={"patient_id": patient["id"], "slot_id": slot_id})
    booking_id = booking_resp.json()["id"]

    # 2. Delete Doctor
    response = client.delete(f"/users/doctors/{doctor_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # 3. Verify Cascade: Slots should be gone
    slot_resp = client.get(f"/slots/{slot_id}")
    assert slot_resp.status_code == status.HTTP_404_NOT_FOUND

    # 4. Verify Cascade: Bookings should be gone
    booking_resp = client.get(f"/bookings/{booking_id}")
    assert booking_resp.status_code == status.HTTP_404_NOT_FOUND
