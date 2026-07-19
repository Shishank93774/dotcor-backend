from typing import Annotated, Literal

from app.schemas.user import UserBase, UserCreate, UserReadPrivate, UserReadPublic
from pydantic import ConfigDict, Field


class DoctorBase(UserBase):
    role: Literal["doctor"] = "doctor"
    specialization: Annotated[str, Field(..., min_length=5)]


class DoctorCreate(UserCreate, DoctorBase):
    pass


class DoctorReadPublic(UserReadPublic, DoctorBase):
    model_config = ConfigDict(from_attributes=True)


class DoctorReadPrivate(UserReadPrivate, DoctorBase):
    model_config = ConfigDict(from_attributes=True)
