from app.db.connection import get_db
from app.services.auth import AuthService
from app.services.booking import BookingService
from app.services.chat_room import ChatRoomService
from app.services.doctor import DoctorService
from app.services.message import MessageService
from app.services.patient import PatientService
from app.services.slot import SlotService
from app.services.user import UserService
from fastapi import Depends
from sqlalchemy.orm import Session


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db=db)


def get_patient_service(db: Session = Depends(get_db)) -> PatientService:
    return PatientService(db=db)


def get_slot_service(db: Session = Depends(get_db)) -> SlotService:
    return SlotService(db=db)


def get_doctor_service(db: Session = Depends(get_db)) -> DoctorService:
    return DoctorService(db=db)


def get_booking_service(db: Session = Depends(get_db)) -> BookingService:
    return BookingService(db=db)


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db=db)


def get_message_service(db: Session = Depends(get_db)) -> MessageService:
    return MessageService(db=db)


def get_chat_room_service(db: Session = Depends(get_db)) -> ChatRoomService:
    return ChatRoomService(db=db)
