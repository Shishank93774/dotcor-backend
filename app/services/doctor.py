from app.core.utils import get_password_hash
from app.db.models.doctor import Doctor
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from fastapi import HTTPException

class DoctorService:
    def __init__(self, db: Session):
        self._db = db

    def list_doctors(self) -> list[Doctor]:
        return self._db.scalars(select(Doctor)).all()

    def get_doctor(self, doctor_id: int) -> Doctor | None:
        return self._db.scalars(select(Doctor).where(Doctor.id == doctor_id)).first()

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
            raise HTTPException(status_code=422, detail="Username, email, or contact number already exists")
        except SQLAlchemyError:
            self._db.rollback()
            raise HTTPException(status_code=500, detail="An unexpected database error occurred while creating the doctor")
