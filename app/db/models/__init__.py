# app/db/models/__init__.py
from app.db.models.booking import Booking
from app.db.models.doctor import Doctor
from app.db.models.patient import Patient
from app.db.models.slot import Slot
from app.db.models.user import User

__all__ = ["User", "Doctor", "Patient", "Slot", "Booking"]
