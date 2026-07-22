from app.db.models.booking import Booking
from sqlalchemy import select
from sqlalchemy.orm import Session


class BookingService:
    def __init__(self, db: Session):
        self._db = db

    def list_bookings(self) -> list[Booking]:
        return self._db.scalars(select(Booking)).all()

    def get_booking(self, booking_id: int) -> Booking | None:
        return self._db.scalars(select(Booking).where(Booking.id == booking_id)).first()

    def create_booking(self, patient_id: int, slot_id: int) -> Booking:
        booking = Booking(patient_id=patient_id, slot_id=slot_id, status="booked")
        self._db.add(booking)
        self._db.commit()
        self._db.refresh(booking)

        return booking

    def cancel_booking(self, booking_id: int) -> None:
        booking = self.get_booking(booking_id)
        if not booking:
            return None
        booking.status = "cancelled"
        self._db.commit()
        self._db.refresh(booking)

        return booking
