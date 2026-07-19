# app/schemas/__init__.py
from app.schemas.booking import BookingCreate, BookingRead
from app.schemas.doctor import DoctorCreate, DoctorReadPrivate, DoctorReadPublic
from app.schemas.patient import PatientCreate, PatientReadPrivate, PatientReadPublic
from app.schemas.slot import SlotCreate, SlotRead
from app.schemas.user import UserCreate, UserReadPrivate, UserReadPublic

__all__ = [
    "UserCreate",
    "UserReadPublic",
    "UserReadPrivate",
    "PatientCreate",
    "PatientReadPublic",
    "PatientReadPrivate",
    "DoctorCreate",
    "DoctorReadPublic",
    "DoctorReadPrivate",
    "SlotCreate",
    "SlotRead",
    "BookingCreate",
    "BookingRead",
]
