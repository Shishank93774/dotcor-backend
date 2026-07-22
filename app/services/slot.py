from datetime import datetime

from app.db.models.slot import Slot
from sqlalchemy import select
from sqlalchemy.orm import Session


class SlotService:
    def __init__(self, db: Session):
        self._db = db

    def list_slots(self) -> list[Slot]:
        return self._db.scalars(select(Slot)).all()

    def get_slot(self, slot_id: int) -> Slot | None:
        return self._db.scalars(select(Slot).where(Slot.id == slot_id)).first()

    def create_slot(self, doctor_id: int, start_time: datetime, end_time: datetime) -> Slot:
        slot = Slot(doctor_id=doctor_id, start_time=start_time, end_time=end_time)
        self._db.add(slot)
        self._db.commit()
        self._db.refresh(slot)

        return slot

    def delete_slot(self, slot_id: int) -> Slot | None:
        slot = self.get_slot(slot_id)
        if not slot:
            return None
        self._db.delete(slot)
        self._db.commit()

        return slot
