from datetime import datetime

from app.core.exceptions import InvalidInputError, ResourceNotFoundError
from app.db.models.slot import Slot
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


class SlotService:
    def __init__(self, db: Session):
        self._db = db

    def list_slots(self, doctor_id: int | None) -> list[Slot]:
        query = select(Slot)
        if doctor_id is not None:
            from app.services.doctor import DoctorService

            # Check if doctor exists
            doctor_service = DoctorService(db=self._db)
            doctor_service.get_doctor(doctor_id)

            query = query.where(Slot.doctor_id == doctor_id)

        return self._db.scalars(query).all()

    def get_slot(self, slot_id: int) -> Slot:
        slot = self._db.scalars(select(Slot).where(Slot.id == slot_id)).first()
        if not slot:
            raise ResourceNotFoundError("Slot not found")

        return slot

    def create_slot(self, doctor_id: int, start_time: datetime, end_time: datetime) -> Slot:
        try:
            from app.services.doctor import DoctorService

            doctor_service = DoctorService(db=self._db)
            # Check if doctor exists
            doctor_service.get_doctor(doctor_id)
            slot = Slot(doctor_id=doctor_id, start_time=start_time, end_time=end_time)
            self._db.add(slot)
            self._db.commit()
            self._db.refresh(slot)
            return slot
        except IntegrityError:
            self._db.rollback()
            raise InvalidInputError("Invalid slot range, overlapping slot, or doctor not found")

    def delete_slot(self, slot_id: int) -> None:
        slot = self.get_slot(slot_id)
        self._db.delete(slot)
        self._db.commit()
        return None
