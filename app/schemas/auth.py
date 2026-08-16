from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class AuthBase(BaseModel):
    user_id: Annotated[int, Field(...)]


class AuthCreate(AuthBase):
    pass


class AuthRead(AuthBase):
    id: Annotated[int, Field(...)]
    token: Annotated[str, Field(...)]

    model_config = ConfigDict(from_attributes=True)
