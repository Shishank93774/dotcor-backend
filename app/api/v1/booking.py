from app.core.services import get_booking_service
from app.schemas.booking import BookingCreate, BookingRead
from app.services.booking import BookingService
from fastapi import APIRouter, Depends, status

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("/", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
def create_booking(booking: BookingCreate, booking_service: BookingService = Depends(get_booking_service)):
    return booking_service.create_booking(**booking.model_dump())


@router.get("/{booking_id}", response_model=BookingRead, status_code=status.HTTP_200_OK)
def get_booking(booking_id: int, booking_service: BookingService = Depends(get_booking_service)):
    return booking_service.get_booking(booking_id)


@router.get("/", response_model=list[BookingRead], status_code=status.HTTP_200_OK)
def get_bookings(booking_service: BookingService = Depends(get_booking_service)):
    return booking_service.list_bookings()


@router.patch("/cancel", response_model=BookingRead, status_code=status.HTTP_200_OK)
def cancel_booking(booking_id: int, booking_service: BookingService = Depends(get_booking_service)):
    return booking_service.cancel_booking(booking_id)


@router.delete("/{booking_id}", response_model=None, status_code=status.HTTP_204_NO_CONTENT)
def delete_booking(booking_id: int, booking_service: BookingService = Depends(get_booking_service)):
    return booking_service.delete_booking(booking_id)
