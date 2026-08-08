from app.core.services import get_slot_service
from app.schemas.slot import SlotCreate, SlotRead
from app.services.slot import SlotService
from fastapi import APIRouter, Depends, status

router = APIRouter(prefix="/slots", tags=["slots"])


@router.post("/", response_model=SlotRead, status_code=status.HTTP_201_CREATED)
def create_slot(req_slot: SlotCreate, slot_service: SlotService = Depends(get_slot_service)):
    return slot_service.create_slot(**req_slot.model_dump())


@router.get("/{slot_id}", response_model=SlotRead, status_code=status.HTTP_200_OK)
def get_slot(slot_id: int, slot_service: SlotService = Depends(get_slot_service)):
    return slot_service.get_slot(slot_id)


@router.get("/", response_model=list[SlotRead], status_code=status.HTTP_200_OK)
def get_slots(doctor_id: int = None, slot_service: SlotService = Depends(get_slot_service)):
    return slot_service.list_slots(doctor_id=doctor_id)


@router.delete("/{slot_id}", response_model=None, status_code=status.HTTP_204_NO_CONTENT)
def delete_slot(slot_id: int, slot_service: SlotService = Depends(get_slot_service)):
    return slot_service.delete_slot(slot_id)
