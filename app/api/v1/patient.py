from app.core.services import get_patient_service
from app.schemas.booking import BookingRead
from app.schemas.patient import PatientCreate, PatientReadPrivate, PatientReadPublic
from app.services.patient import PatientService
from fastapi import APIRouter, Depends, status

router = APIRouter(prefix="/users/patients", tags=["patients"])


@router.post("/", response_model=PatientReadPrivate, status_code=status.HTTP_201_CREATED)
def create_patient(patient: PatientCreate, patient_service: PatientService = Depends(get_patient_service)):
    return patient_service.create_patient(**patient.model_dump())


@router.get("/{patient_id}", response_model=PatientReadPrivate, status_code=status.HTTP_200_OK)
def get_patient(patient_id: int, patient_service: PatientService = Depends(get_patient_service)):
    return patient_service.get_patient(patient_id)


@router.get("/", response_model=list[PatientReadPublic], status_code=status.HTTP_200_OK)
def get_patients(patient_service: PatientService = Depends(get_patient_service)):
    return patient_service.list_patients()


@router.get("/{patient_id}/bookings", response_model=list[BookingRead], status_code=status.HTTP_200_OK)
def get_bookings(patient_id: int, patient_service: PatientService = Depends(get_patient_service)):
    patient = patient_service.get_patient(patient_id)
    return patient.bookings
