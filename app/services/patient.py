from app.core.exceptions import ResourceConflictError, ResourceNotFoundError, ServiceError
from app.core.utils import get_password_hash
from app.db.models.patient import Patient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session


class PatientService:
    def __init__(self, db: Session):
        self._db = db

    def list_patients(self) -> list[Patient]:
        return self._db.scalars(select(Patient)).all()

    def get_patient(self, patient_id: int) -> Patient:
        patient = self._db.scalars(select(Patient).where(Patient.id == patient_id)).first()
        if not patient:
            raise ResourceNotFoundError("Patient not found")
        return patient

    def create_patient(self, username: str, email: str, password: str, contact_number: str, role: str = "patient") -> Patient:
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
            return patient
        except IntegrityError:
            self._db.rollback()
            raise ResourceConflictError("Username, email, or contact number already exists")
        except SQLAlchemyError:
            self._db.rollback()
            raise ServiceError("An unexpected database error occurred while creating the patient")
