from app.db.models.booking import Booking
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


class BookingService:
    def __init__(self, db: Session):
        self._db = db

    def list_bookings(self) -> list[Booking]:
        return self._db.scalars(select(Booking)).all()

    def get_booking(self, booking_id: int) -> Booking | None:
        return self._db.scalars(select(Booking).where(Booking.id == booking_id)).first()

    def create_booking(self, patient_id: int, slot_id: int) -> Booking:
        try:
            booking = Booking(patient_id=patient_id, slot_id=slot_id, status="booked")
            # Check if booking already exists
            previous_booking = self._db.scalars(select(Booking).where(Booking.slot_id == slot_id, Booking.status == "booked")).first()
            if previous_booking:
                raise HTTPException(status_code=409, detail="Slot already booked")
            self._db.add(booking)
            self._db.commit()
            self._db.refresh(booking)
            return booking
        except IntegrityError:
            self._db.rollback()
            raise HTTPException(status_code=409, detail="Invalid patient/slot ID")

    def cancel_booking(self, booking_id: int) -> Booking | None:
        booking = self.get_booking(booking_id)
        if not booking:
            return None
        booking.status = "cancelled"
        self._db.commit()
        self._db.refresh(booking)

        return booking
