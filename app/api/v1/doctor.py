from app.db.connection import get_db
from app.schemas.doctor import DoctorCreate, DoctorReadPrivate, DoctorReadPublic
from app.schemas.slot import SlotRead
from app.services.doctor import DoctorService
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/users/doctors", tags=["doctors"])


def get_doctor_service(db: Session = Depends(get_db)) -> DoctorService:
    return DoctorService(db=db)


@router.post("/", response_model=DoctorReadPrivate, status_code=status.HTTP_201_CREATED)
def create_doctor(doctor: DoctorCreate, doctor_service: DoctorService = Depends(get_doctor_service)):
    return doctor_service.create_doctor(**doctor.model_dump())


@router.get("/{doctor_id}", response_model=DoctorReadPrivate, status_code=status.HTTP_200_OK)
def get_doctor(doctor_id: int, doctor_service: DoctorService = Depends(get_doctor_service)):
    return doctor_service.get_doctor(doctor_id)


@router.get("/", response_model=list[DoctorReadPublic], status_code=status.HTTP_200_OK)
def get_doctors(doctor_service: DoctorService = Depends(get_doctor_service)):
    return doctor_service.list_doctors()


@router.get("/{doctor_id}/slots", response_model=list[SlotRead], status_code=status.HTTP_200_OK)
def get_slots(doctor_id: int, doctor_service: DoctorService = Depends(get_doctor_service)):
    doctor = doctor_service.get_doctor(doctor_id)
    return doctor.slots
