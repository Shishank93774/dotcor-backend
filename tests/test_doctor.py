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


def test_delete_doctor_not_found(client):
    response = client.delete("/users/doctors/9999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
