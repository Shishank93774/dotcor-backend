from app.core.exceptions import InvalidInputError, ResourceConflictError, ResourceNotFoundError
from app.db.models.booking import Booking
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


class BookingService:
    def __init__(self, db: Session):
        self._db = db

    def list_bookings(self) -> list[Booking]:
        return self._db.scalars(select(Booking)).all()

    def get_booking(self, booking_id: int) -> Booking:
        booking = self._db.scalars(select(Booking).where(Booking.id == booking_id)).first()
        if not booking:
            raise ResourceNotFoundError("Booking not found")
        return booking

    def create_booking(self, patient_id: int, slot_id: int) -> Booking:
        try:
            booking = Booking(patient_id=patient_id, slot_id=slot_id, status="booked")
            # Check if booking already exists
            previous_booking = self._db.scalars(select(Booking).where(Booking.slot_id == slot_id, Booking.status == "booked")).first()
            if previous_booking:
                raise ResourceConflictError("Slot already booked")
            import time

            time.sleep(0.5)
            self._db.add(booking)
            self._db.commit()
            self._db.refresh(booking)
            return booking
        except IntegrityError:
            self._db.rollback()
            raise InvalidInputError("Invalid patient/slot ID")

    def cancel_booking(self, booking_id: int) -> Booking:
        booking = self.get_booking(booking_id)
        if not booking:
            raise ResourceNotFoundError("Booking not found")
        booking.status = "cancelled"
        self._db.commit()
        self._db.refresh(booking)

        return booking
