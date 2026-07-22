from app.db.connection import get_db
from app.schemas.booking import BookingCreate, BookingRead
from app.services.booking import BookingService
from app.services.patient import PatientService
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter(prefix="/bookings")


def get_patient_service(db: Session = Depends(get_db)) -> PatientService:
    return PatientService(db=db)


def get_booking_service(db: Session = Depends(get_db)) -> BookingService:
    return BookingService(db=db)


@router.post("/", response_model=BookingRead)
def create_booking(
    booking: BookingCreate,
    patient_service: PatientService = Depends(get_patient_service),
    booking_service: BookingService = Depends(get_booking_service),
):
    patient = patient_service.get_patient(booking.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return booking_service.create_booking(**booking.model_dump())


@router.get("/{booking_id}", response_model=BookingRead)
def get_booking(booking_id: int, booking_service: BookingService = Depends(get_booking_service)):
    return booking_service.get_booking(booking_id)


@router.get("/", response_model=list[BookingRead])
def get_bookings(booking_service: BookingService = Depends(get_booking_service)):
    return booking_service.list_bookings()


@router.patch("/cancel", response_model=BookingRead | None)
def cancel_booking(booking_id: int, booking_service: BookingService = Depends(get_booking_service)):
    return booking_service.cancel_booking(booking_id)
