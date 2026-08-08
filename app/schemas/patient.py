from typing import Literal

from app.schemas.user import UserBase, UserCreate, UserReadPrivate, UserReadPublic
from pydantic import ConfigDict


class PatientBase(UserBase):
    role: Literal["patient"] = "patient"


class PatientCreate(UserCreate, PatientBase):
    pass


class PatientReadPublic(UserReadPublic, PatientBase):
    model_config = ConfigDict(from_attributes=True)


class PatientReadPrivate(UserReadPrivate, PatientBase):
    model_config = ConfigDict(from_attributes=True)
