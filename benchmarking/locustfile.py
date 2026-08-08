import json
from dataclasses import dataclass
from json import JSONDecodeError
from pathlib import Path
from random import randint
from typing import List

from locust import HttpUser, between, events, task


@dataclass
class BenchmarkData:
    doctors: List[dict]
    slots: List[dict]
    patients: List[dict]
    hot_slots: List[dict]


CWD = Path(__file__).parent.resolve()
DOCTOR_FILE_PATH = CWD / "json_files/doctors.json"
SLOT_FILE_PATH = CWD / "json_files/slots.json"
PATIENT_FILE_PATH = CWD / "json_files/patients.json"


@events.init.add_listener
def on_locust_init(environment, **kwargs):
    doctors = []
    slots = []
    patients = []

    with open(DOCTOR_FILE_PATH) as f:
        for line in f:
            try:
                doctors.append(json.loads(line))
            except JSONDecodeError:
                pass

    with open(SLOT_FILE_PATH) as f:
        for line in f:
            try:
                slots.append(json.loads(line))
            except JSONDecodeError:
                pass

    with open(PATIENT_FILE_PATH) as f:
        for line in f:
            try:
                patients.append(json.loads(line))
            except JSONDecodeError:
                pass

    if not doctors or not slots or not patients:
        raise RuntimeError(f"Seed data is missing. Doctors: {len(doctors)}, Slots: {len(slots)}, Patients: {len(patients)}. Run init.py first.")

    environment.shared_state = BenchmarkData(
        doctors=doctors,
        slots=slots,
        patients=patients,
        hot_slots=slots[:10],
    )


class WebsiteUser(HttpUser):
    wait_time = between(1, 5)

    @task
    def random_booking(self):
        state = self.environment.shared_state
        self.client.post(
            "/bookings/",
            name="random_booking",
            json={
                "doctor_id": state.doctors[randint(0, len(state.doctors) - 1)]["id"],
                "patient_id": state.patients[randint(0, len(state.patients) - 1)]["id"],
                "slot_id": state.slots[randint(0, len(state.slots) - 1)]["id"],
            },
        )

    @task
    def hot_slots_booking(self):
        state = self.environment.shared_state
        self.client.post(
            "/bookings/",
            name="hot_slots_booking",
            json={
                "doctor_id": state.doctors[randint(0, len(state.doctors) - 1)]["id"],
                "patient_id": state.patients[randint(0, len(state.patients) - 1)]["id"],
                "slot_id": state.hot_slots[randint(0, len(state.hot_slots) - 1)]["id"],
            },
        )
