from datetime import datetime

from app.db.models.slot import Slot
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session


class SlotService:
    def __init__(self, db: Session):
        self._db = db

    def list_slots(self) -> list[Slot]:
        return self._db.scalars(select(Slot)).all()

    def get_slot(self, slot_id: int) -> Slot | None:
        return self._db.scalars(select(Slot).where(Slot.id == slot_id)).first()

    def create_slot(self, doctor_id: int, start_time: datetime, end_time: datetime) -> Slot:
        try:
            slot = Slot(doctor_id=doctor_id, start_time=start_time, end_time=end_time)
            self._db.add(slot)
            self._db.commit()
            self._db.refresh(slot)
            return slot
        except IntegrityError:
            self._db.rollback()
            raise HTTPException(status_code=422, detail="Invalid slot range, overlapping slot, or doctor not found")
        except SQLAlchemyError:
            self._db.rollback()
            raise HTTPException(status_code=500, detail="An unexpected database error occurred while creating the slot")

    def delete_slot(self, slot_id: int) -> Slot | None:
        try:
            slot = self.get_slot(slot_id)
            if not slot:
                return None
            self._db.delete(slot)
            self._db.commit()
            return slot
        except SQLAlchemyError:
            self._db.rollback()
            raise HTTPException(status_code=500, detail="An unexpected database error occurred while deleting the slot")
