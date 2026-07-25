from datetime import datetime, timedelta

from fastapi import status


def test_create_slot(client, create_doctor):
    doctor = create_doctor()
    start = (datetime.now() + timedelta(days=2)).isoformat()
    end = (datetime.now() + timedelta(days=2, hours=1)).isoformat()
    payload = {"doctor_id": doctor.id, "start_time": start, "end_time": end}
    response = client.post("/slots/", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["doctor_id"] == doctor.id
    assert "id" in data


def test_create_slot_overlap(client, create_doctor, create_slot):
    doctor = create_doctor()
    start = datetime.now() + timedelta(days=3)
    end = start + timedelta(hours=1)
    # Create first slot
    create_slot(doctor_id=doctor.id, start_time=start, end_time=end)
    # Try to create overlapping slot (same doctor, same time)
    payload = {"doctor_id": doctor.id, "start_time": start.isoformat(), "end_time": end.isoformat()}
    response = client.post("/slots/", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "overlapping" in response.text.lower() or "slot" in response.text.lower()


def test_get_slots(client, create_slot):
    slot = create_slot()
    response = client.get(f"/slots/{slot.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == slot.id


def test_list_slots(client, create_slot):
    create_slot()  # creates one with default doctor
    response = client.get("/slots/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) >= 1


def test_list_slots_by_doctor(client, create_doctor, create_slot):
    doctor1 = create_doctor(username="docA")
    doctor2 = create_doctor(username="docB")
    slot1 = create_slot(doctor_id=doctor1.id)
    slot2 = create_slot(doctor_id=doctor2.id)  # noqa: F841
    response = client.get(f"/slots/?doctor_id={doctor1.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == slot1.id


def test_delete_slot(client, create_slot):
    slot = create_slot()
    response = client.delete(f"/slots/{slot.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == slot.id
    # Verify it's gone
    response = client.get(f"/slots/{slot.id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_slot_not_found(client):
    response = client.delete("/slots/9999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
