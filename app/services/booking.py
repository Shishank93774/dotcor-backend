from app.core.config import config
from app.core.exceptions import InvalidInputError, ResourceConflictError, ResourceNotFoundError
from app.core.logging import get_logger
from app.db.models.booking import Booking
from app.db.models.slot import Slot
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

logger = get_logger(__name__)

CONFLICT_HANDLE_MODE = config.CONFLICT_HANDLE_MODE


class BookingService:
    def __init__(self, db: Session):
        self._db = db

    def list_bookings(self) -> list[Booking]:
        return self._db.scalars(select(Booking)).all()

    def get_booking(self, booking_id: int) -> Booking:
        booking = self._db.scalars(select(Booking).where(Booking.id == booking_id)).first()
        if not booking:
            logger.warning(f"Booking with ID {booking_id} not found")
            raise ResourceNotFoundError("Booking not found")
        return booking

    def _create_booking_pessimistic(self, patient_id: int, slot_id: int) -> Booking:
        try:
            from app.services.patient import PatientService

            # Check if patient exists
            patient_service = PatientService(db=self._db)
            patient_service.get_patient(patient_id)

            # Hold slot to try booking
            slot = self._db.scalars(select(Slot).where(Slot.id == slot_id).with_for_update()).first()
            if not slot:
                raise ResourceNotFoundError("Slot not found")

            # Check if booking already exists
            previous_booking = self._db.scalars(select(Booking).where(Booking.slot_id == slot_id, Booking.status == "booked")).first()
            if previous_booking:
                raise ResourceConflictError("Slot already booked")

            booking = Booking(patient_id=patient_id, slot_id=slot_id, status="booked")
            self._db.add(booking)
            self._db.commit()
            self._db.refresh(booking)
            logger.info(f"Pessimistic booking created: {booking.id} for patient {patient_id} on slot {slot_id}")
            return booking
        except IntegrityError as e:
            self._db.rollback()
            logger.error(f"Integrity error during pessimistic booking for patient {patient_id} on slot {slot_id}.\n Error: {e}")
            raise InvalidInputError("Invalid patient/slot ID")

    def _create_booking_optimistic(self, patient_id: int, slot_id: int) -> Booking:
        try:
            from app.services.patient import PatientService

            # Check if patient exists
            patient_service = PatientService(db=self._db)
            patient_service.get_patient(patient_id)

            # Check if slot exists
            slot = self._db.scalars(select(Slot).where(Slot.id == slot_id)).first()
            if not slot:
                raise ResourceNotFoundError("Slot not found")

            # Check if booking already exists
            previous_booking = self._db.scalars(select(Booking).where(Booking.slot_id == slot_id, Booking.status == "booked")).first()
            if previous_booking:
                raise ResourceConflictError("Slot already booked")

            booking = Booking(patient_id=patient_id, slot_id=slot_id, status="booked")
            self._db.add(booking)
            from datetime import UTC, datetime

            slot.updated_at = datetime.now(UTC)  # Touch slot to update version
            self._db.flush()  # Try to insert booking

            self._db.commit()

            self._db.refresh(booking)
            logger.info(f"Optimistic booking created: {booking.id} for patient {patient_id} on slot {slot_id}")
            return booking
        except StaleDataError as e:
            self._db.rollback()
            logger.info(f"OCC Conflict: slot {slot_id} was modified by another transaction.\n Error: {e}")
            raise ResourceConflictError("Slot already booked")
        except IntegrityError as e:
            self._db.rollback()
            logger.error(f"Integrity error during optimistic booking for patient {patient_id} on slot {slot_id}.\n Error: {e}")
            raise InvalidInputError("Invalid patient/slot ID")

    def create_booking(self, patient_id: int, slot_id: int) -> Booking:
        if CONFLICT_HANDLE_MODE == "optimistic":
            return self._create_booking_optimistic(patient_id, slot_id)
        return self._create_booking_pessimistic(patient_id, slot_id)

    def cancel_booking(self, booking_id: int) -> Booking:
        booking = self.get_booking(booking_id)
        booking.status = "cancelled"
        self._db.commit()
        self._db.refresh(booking)
        logger.info(f"Cancelled booking ID: {booking_id}")

        return booking

    def delete_booking(self, booking_id: int) -> None:
        booking = self.get_booking(booking_id)
        self._db.delete(booking)
        self._db.commit()
        logger.info(f"Deleted booking ID: {booking_id}")

        return None
