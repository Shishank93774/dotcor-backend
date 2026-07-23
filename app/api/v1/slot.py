from app.db.connection import get_db
from app.schemas.slot import SlotCreate, SlotRead
from app.services.doctor import DoctorService
from app.services.slot import SlotService
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter(prefix="/slots")


def get_doctor_service(db: Session = Depends(get_db)) -> DoctorService:
    return DoctorService(db=db)


def get_slot_service(db: Session = Depends(get_db)) -> SlotService:
    return SlotService(db=db)


@router.post("/", response_model=SlotRead)
def create_slot(
    req_slot: SlotCreate,
    doctor_service: DoctorService = Depends(get_doctor_service),
    slot_service: SlotService = Depends(get_slot_service),
):
    doctor = doctor_service.get_doctor(req_slot.doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    slot = slot_service.create_slot(**req_slot.model_dump())

    return slot


@router.get("/{slot_id}", response_model=SlotRead)
def get_slot(slot_id: int, slot_service: SlotService = Depends(get_slot_service)):
    slot = slot_service.get_slot(slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    return slot


@router.get("/", response_model=list[SlotRead])
def get_slots(slot_service: SlotService = Depends(get_slot_service)):
    return slot_service.list_slots()


@router.delete("/", response_model=SlotRead)
def delete_slot(slot_id: int, slot_service: SlotService = Depends(get_slot_service)):
    slot = slot_service.delete_slot(slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    return slot
