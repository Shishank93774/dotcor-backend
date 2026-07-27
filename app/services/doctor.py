from app.core.exceptions import ResourceConflictError, ResourceNotFoundError
from app.core.utils import get_password_hash
from app.db.models.doctor import Doctor
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


class DoctorService:
    def __init__(self, db: Session):
        self._db = db

    def list_doctors(self) -> list[Doctor]:
        return self._db.scalars(select(Doctor)).all()

    def get_doctor(self, doctor_id: int) -> Doctor:
        doctor = self._db.scalars(select(Doctor).where(Doctor.id == doctor_id)).first()
        if not doctor:
            raise ResourceNotFoundError("Doctor not found")
        return doctor

    def create_doctor(self, username: str, email: str, password: str, contact_number: str, specialization: str, role: str = "doctor") -> Doctor:
        try:
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
        except IntegrityError:
            self._db.rollback()
            raise ResourceConflictError("Username, email, or contact number already exists")
