from app.core.exceptions import ResourceConflictError, ResourceNotFoundError
from app.core.logging import get_logger
from app.db.models.doctor import Doctor
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

logger = get_logger(__name__)


class DoctorService:
    def __init__(self, db: Session):
        self._db = db

    def list_doctors(self) -> list[Doctor]:
        return self._db.scalars(select(Doctor)).all()

    def get_doctor(self, doctor_id: int) -> Doctor:
        doctor = self._db.scalars(select(Doctor).where(Doctor.id == doctor_id)).first()
        if not doctor:
            logger.warning(f"Doctor with ID {doctor_id} not found")
            raise ResourceNotFoundError("Doctor not found")
        return doctor

    def create_doctor(self, username: str, email: str, password: str, contact_number: str, specialization: str, role: str = "doctor") -> Doctor:
        from app.core.utils import get_password_hash

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
            logger.info(f"Created doctor: {username} (ID: {doctor.id})")
            return doctor
        except IntegrityError as e:
            self._db.rollback()
            logger.error(f"Conflict creating doctor: {username} - {email}.\n Error: {e}")
            raise ResourceConflictError("Username, email, or contact number already exists")

    def delete_doctor(self, doctor_id: int) -> None:
        doctor = self.get_doctor(doctor_id)
        self._db.delete(doctor)
        self._db.commit()
        logger.info(f"Deleted doctor ID: {doctor_id}")

        return None
