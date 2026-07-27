import asyncio

import httpx
import pytest
from app.core.utils import get_password_hash
from app.db.connection import SessionLocal
from app.db.models.doctor import Doctor
from app.db.models.patient import Patient
from app.db.models.slot import Slot
from app.main import app
from fastapi import status


@pytest.mark.asyncio
@pytest.mark.xfail(reason="Haven't implemented concurrent proof system yet")
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
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
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
@pytest.mark.xfail(reason="Haven't implemented concurrent proof system yet")
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
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            tasks = [client.post("/bookings/", json={"patient_id": p, "slot_id": slot_id}) for p in patient_ids]
            await asyncio.gather(*tasks)
    finally:
        pass

    # 2. Verify DB state
    with SessionLocal() as session:
        stmt = select(Booking).where(Booking.slot_id == slot_id, Booking.status == "booked")
        result = session.scalars(stmt).all()
        assert len(result) == 1, f"Database corruption: {len(result)} active bookings found for one slot"
