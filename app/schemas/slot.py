from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class SlotBase(BaseModel):
    doctor_id: Annotated[int, Field(...)]
    start_time: Annotated[datetime, Field(...)]
    end_time: Annotated[datetime, Field(...)]


class SlotCreate(SlotBase):
    pass


class SlotRead(SlotBase):
    id: Annotated[int, Field(...)]

    model_config = ConfigDict(from_attributes=True)
