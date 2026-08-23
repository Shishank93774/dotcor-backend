from typing import Annotated

from app.schemas.message import MessageRead
from pydantic import BaseModel, Field


class ChatRoomBase(BaseModel):
    pass


class ChatRoomCreate(ChatRoomBase):
    patient_id: Annotated[int, Field(...)]
    doctor_id: Annotated[int, Field(...)]
    booking_id: Annotated[int, Field(...)]


class ChatRoomRead(ChatRoomCreate):
    id: Annotated[int, Field(...)]
