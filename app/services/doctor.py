from app.core.utils import get_password_hash
from app.db.models.doctor import Doctor
from sqlalchemy import select
from sqlalchemy.orm import Session


class DoctorService:
    def __init__(self, db: Session):
        self._db = db

    def list_doctors(self) -> list[Doctor]:
        return self._db.scalars(select(Doctor)).all()

    def get_doctor(self, doctor_id: int) -> Doctor | None:
        return self._db.scalars(select(Doctor).where(Doctor.id == doctor_id)).first()

    def create_doctor(self, username: str, email: str, password: str, contact_number: str, specialization: str, role: str = "doctor") -> Doctor:
        doctor = Doctor(
            username=username,
            email=email,
            hashed_password=get_password_hash(password.get_secret_value()),
            contact_number=contact_number,
            specialization=specialization,
            role=role,
        )
        self._db.add(doctor)
        self._db.commit()
        self._db.refresh(doctor)

        return doctor
