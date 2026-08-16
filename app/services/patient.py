from app.core.exceptions import ResourceConflictError, ResourceNotFoundError
from app.core.logging import get_logger
from app.db.models.patient import Patient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

logger = get_logger(__name__)


class PatientService:
    def __init__(self, db: Session):
        self._db = db

    def list_patients(self) -> list[Patient]:
        return self._db.scalars(select(Patient)).all()

    def get_patient(self, patient_id: int) -> Patient:
        patient = self._db.scalars(select(Patient).where(Patient.id == patient_id)).first()
        if not patient:
            logger.warning(f"Patient with ID {patient_id} not found")
            raise ResourceNotFoundError("Patient not found")
        return patient

    def create_patient(self, username: str, email: str, password: str, contact_number: str, role: str = "patient") -> Patient:
        from app.core.utils import get_password_hash

        try:
            patient = Patient(
                username=username,
                email=email,
                hashed_password=get_password_hash(password.get_secret_value()),
                contact_number=contact_number,
                role=role,
            )
            self._db.add(patient)
            self._db.commit()
            self._db.refresh(patient)
            logger.info(f"Created patient: {username} (ID: {patient.id})")
            return patient
        except IntegrityError as e:
            self._db.rollback()
            logger.error(f"Conflict creating patient: {username} - {email}.\n Error: {e}")
            raise ResourceConflictError("Username, email, or contact number already exists")

    def delete_patient(self, patient_id: int) -> None:
        patient = self.get_patient(patient_id)
        self._db.delete(patient)
        self._db.commit()
        logger.info(f"Deleted patient ID: {patient_id}")

        return None
