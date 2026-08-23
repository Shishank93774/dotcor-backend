import asyncio

import httpx2
import pytest
from app.core.utils import get_password_hash
from app.db.connection import SessionLocal
from app.db.models.doctor import Doctor
from app.db.models.patient import Patient
from app.db.models.slot import Slot
from app.main import app
from fastapi import status


@pytest.mark.asyncio
async def test_concurrent_booking_single_winner():
    N = 75
    # 1. Setup: Create data using a real session to ensure persistence
    with SessionLocal() as session:
        # Create Doctor
        doctor = Doctor(
            username="concurrency_doc",
            email="concurrency_doc@example.com",
            hashed_password=get_password_hash("secret"),
            contact_number="+910000000000",
            specialization="General",
        )
        session.add(doctor)
        session.commit()
        session.refresh(doctor)

        # Create Slot
        import datetime
        from datetime import UTC, timedelta

        start = datetime.datetime.now(UTC) + timedelta(days=1)
        end = start + timedelta(hours=1)
        slot = Slot(doctor_id=doctor.id, start_time=start, end_time=end)
        session.add(slot)
        session.commit()
        slot_id = slot.id

        # Create N Patients
        patient_ids = []
        for i in range(N):
            p = Patient(
                username=f"pat_conc_{i}",
                email=f"pat_conc_{i}@example.com",
                hashed_password=get_password_hash("secret"),
                contact_number=f"+91 7899{23 + i}99999"[:10],
            )
            session.add(p)
            session.commit()
            patient_ids.append(p.id)

    # 2. Clear overrides to use the real get_db (new session per request)
    app.dependency_overrides.clear()

    try:
        async with httpx2.AsyncClient(transport=httpx2.ASGITransport(app=app), base_url="http://test") as client:
            # 3. Fire N concurrent booking requests for the same slot
            tasks = [client.post("/bookings/", json={"patient_id": pid, "slot_id": slot_id}) for pid in patient_ids]

            responses = await asyncio.gather(*tasks)

            # 4. Analysis
            status_codes = [r.status_code for r in responses]
            successes = [r for r in responses if r.status_code == status.HTTP_201_CREATED]
            conflicts = [r for r in responses if r.status_code == status.HTTP_409_CONFLICT]
            invalid_inputs = [r for r in responses if r.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT]

            # Exactly one patient should have successfully booked the slot
            assert len(successes) == 1, f"Expected exactly 1 successful booking, got {len(successes)}. Statuses: {status_codes}"

            # All others should be conflicts (409)
            assert len(conflicts) == N - 1, f"Expected 9 conflicts, got {len(conflicts)}. (Invalid Inputs: {len(invalid_inputs)})"
    finally:
        pass


@pytest.mark.asyncio
async def test_concurrent_booking_persistence_check():
    from app.db.models.booking import Booking
    from sqlalchemy import select

    # 1. Setup
    with SessionLocal() as session:
        doctor = Doctor(
            username="persist_doc",
            email="persist_doc@example.com",
            hashed_password=get_password_hash("secret"),
            contact_number="+912222222222",
            specialization="General",
        )
        session.add(doctor)
        session.commit()

        import datetime
        from datetime import UTC, timedelta

        start = datetime.datetime.now(UTC) + timedelta(days=2)
        end = start + timedelta(hours=1)
        slot = Slot(doctor_id=doctor.id, start_time=start, end_time=end)
        session.add(slot)
        session.commit()
        slot_id = slot.id

        patient_ids = []
        for i in range(5):
            p = Patient(
                username=f"persist_pat_{i}",
                email=f"persist_pat_{i}@example.com",
                hashed_password=get_password_hash("secret"),
                contact_number=f"+913333333{i}",
            )
            session.add(p)
            session.commit()
            patient_ids.append(p.id)

    app.dependency_overrides.clear()

    try:
        async with httpx2.AsyncClient(transport=httpx2.ASGITransport(app=app), base_url="http://test") as client:
            tasks = [client.post("/bookings/", json={"patient_id": p, "slot_id": slot_id}) for p in patient_ids]
            await asyncio.gather(*tasks)
    finally:
        pass

    # 2. Verify DB state
    with SessionLocal() as session:
        stmt = select(Booking).where(Booking.slot_id == slot_id, Booking.status == "booked")
        result = session.scalars(stmt).all()
        assert len(result) == 1, f"Database corruption: {len(result)} active bookings found for one slot"


@pytest.mark.asyncio
async def test_concurrent_booking_with_different_slots():
    import datetime
    from datetime import UTC, timedelta

    from app.db.models.booking import Booking
    from sqlalchemy import select

    NUM_CONCURRENT_REQ = 50

    with SessionLocal() as session:
        doctor = Doctor(
            username="diffslots_doc",
            email="diffslots_doc@example.com",
            hashed_password=get_password_hash("secret"),
            contact_number="+914444444444",
            specialization="General",
        )
        session.add(doctor)
        session.commit()
        session.refresh(doctor)

        slots = []
        for i in range(NUM_CONCURRENT_REQ):
            start = datetime.datetime.now(UTC) + timedelta(days=1) + timedelta(hours=i * 2)
            end = start + timedelta(hours=1)
            slot = Slot(doctor_id=doctor.id, start_time=start, end_time=end)
            session.add(slot)
            session.commit()
            slots.append(slot.id)

        patients = []
        for i in range(NUM_CONCURRENT_REQ):
            p = Patient(
                username=f"diffslots_pat_{i}",
                email=f"diffslots_pat_{i}@example.com",
                hashed_password=get_password_hash("secret"),
                contact_number=f"+915555{i:06d}",
            )
            session.add(p)
            session.commit()
            patients.append(p.id)

    app.dependency_overrides.clear()

    async with httpx2.AsyncClient(transport=httpx2.ASGITransport(app=app), base_url="http://test") as client:
        tasks = [client.post("/bookings/", json={"patient_id": pid, "slot_id": sid}) for pid, sid in zip(patients, slots)]
        await asyncio.gather(*tasks)

    with SessionLocal() as session:
        stmt = select(Booking).where(Booking.status == "booked", Booking.patient_id.in_(patients))
        result = session.scalars(stmt).all()
        assert len(result) == NUM_CONCURRENT_REQ, f"Database corruption: {len(result)} active bookings found for {NUM_CONCURRENT_REQ} slots."


def test_concurrent_chat_room_creation_single_winner():
    import threading
    import uuid
    from datetime import UTC, datetime, timedelta

    from sqlalchemy import func, select

    from app.core.utils import get_password_hash
    from app.db.connection import SessionLocal
    from app.db.models.booking import Booking
    from app.db.models.chat_room import ChatRoom
    from app.db.models.doctor import Doctor
    from app.db.models.patient import Patient
    from app.db.models.slot import Slot
    from app.services.chat_room import ChatRoomService

    tag = uuid.uuid4().hex[:8]
    with SessionLocal() as session:
        doctor = Doctor(
            username=f"rr_d_{tag}",
            email=f"rr_d_{tag}@example.com",
            hashed_password=get_password_hash("secret"),
            contact_number=f"+9196000{tag[:3]}",
            specialization="General",
        )
        session.add(doctor)
        session.commit()
        session.refresh(doctor)

        patient = Patient(
            username=f"rr_p_{tag}",
            email=f"rr_p_{tag}@example.com",
            hashed_password=get_password_hash("secret"),
            contact_number=f"+9196001{tag[:5]}",
        )
        session.add(patient)
        session.commit()
        session.refresh(patient)

        start = datetime.now(UTC) + timedelta(days=40)
        slot = Slot(doctor_id=doctor.id, start_time=start, end_time=start + timedelta(hours=1))
        session.add(slot)
        session.commit()
        session.refresh(slot)

        booking = Booking(patient_id=patient.id, slot_id=slot.id, status="booked")
        session.add(booking)
        session.commit()
        session.refresh(booking)

        ids = {"doctor": doctor.id, "patient": patient.id, "booking": booking.id}

    WORKERS = 8
    results = []
    barrier = threading.Barrier(WORKERS)

    def worker():
        session = SessionLocal()
        try:
            barrier.wait(timeout=10)
            room = ChatRoomService(session).create_chat_room(
                patient_id=ids["patient"], doctor_id=ids["doctor"], booking_id=ids["booking"]
            )
            results.append(room.id)
        finally:
            session.close()

    threads = [threading.Thread(target=worker) for _ in range(WORKERS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)
    assert not any(t.is_alive() for t in threads), "chat room race deadlocked"

    assert len(results) == WORKERS
    assert len(set(results)) == 1, f"divergent room ids returned to racing callers: {results}"

    with SessionLocal() as session:
        count = session.scalar(select(func.count()).select_from(ChatRoom).where(ChatRoom.booking_id == ids["booking"]))
        assert count == 1, f"expected exactly one chat room row, found {count}"
