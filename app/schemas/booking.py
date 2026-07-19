from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class BookingBase(BaseModel):
    patient_id: Annotated[int, Field(...)]
    slot_id: Annotated[int, Field(...)]


class BookingCreate(BookingBase):
    pass


class BookingRead(BookingBase):
    id: Annotated[int, Field(...)]
    status: Literal["booked", "cancelled", "completed"] = "booked"

    model_config = ConfigDict(from_attributes=True)
