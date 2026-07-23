from app.db.connection import get_db
from app.schemas.booking import BookingRead
from app.schemas.patient import PatientCreate, PatientReadPrivate, PatientReadPublic
from app.services.patient import PatientService
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter(prefix="/users/patients", tags=["patients"])


def get_patient_service(db: Session = Depends(get_db)) -> PatientService:
    return PatientService(db=db)


@router.post("/", response_model=PatientReadPrivate)
def create_patient(patient: PatientCreate, patient_service: PatientService = Depends(get_patient_service)):
    return patient_service.create_patient(**patient.model_dump())


@router.get("/{patient_id}", response_model=PatientReadPrivate)
def get_patient(patient_id: int, patient_service: PatientService = Depends(get_patient_service)):
    patient = patient_service.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.get("/", response_model=list[PatientReadPublic])
def get_patients(patient_service: PatientService = Depends(get_patient_service)):
    return patient_service.list_patients()


@router.get("/{patient_id}/bookings", response_model=list[BookingRead])
def get_bookings(patient_id: int, patient_service: PatientService = Depends(get_patient_service)):
    patient = patient_service.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient.bookings
