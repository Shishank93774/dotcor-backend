from app.db.connection import get_db
from app.services.booking import BookingService
from app.services.doctor import DoctorService
from app.services.patient import PatientService
from app.services.slot import SlotService
from fastapi import Depends
from sqlalchemy.orm import Session


def get_patient_service(db: Session = Depends(get_db)) -> PatientService:
    return PatientService(db=db)


def get_slot_service(db: Session = Depends(get_db)) -> SlotService:
    return SlotService(db=db)


def get_doctor_service(db: Session = Depends(get_db)) -> DoctorService:
    return DoctorService(db=db)


def get_booking_service(db: Session = Depends(get_db)) -> BookingService:
    return BookingService(db=db)
