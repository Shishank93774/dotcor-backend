from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class MessageBase(BaseModel):
    sender_id: Annotated[int, Field(...)]
    room_id: Annotated[int, Field(...)]
    type: Literal["text", "document"] = "text"
    content: Annotated[str, Field(..., max_length=256)]


class MessageCreate(MessageBase):
    pass


class MessageRead(MessageBase):
    id: Annotated[int, Field(...)]
    updated_at: Annotated[datetime, Field(...)]

    model_config = ConfigDict(from_attributes=True)
