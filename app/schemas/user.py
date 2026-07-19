from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr
from pydantic_extra_types.phone_numbers import PhoneNumber


class UserBase(BaseModel):
    username: Annotated[str, Field(..., min_length=3, max_length=20, pattern="^[a-zA-Z0-9_@]+$")]


class ContactInfo(BaseModel):
    email: EmailStr
    contact_number: Annotated[PhoneNumber, Field(examples=["+1 650-253-0000", "+91 7896256613"])]


class UserCreate(UserBase, ContactInfo):
    password: Annotated[SecretStr, Field(..., min_length=4)]


class UserReadPublic(UserBase):
    model_config = ConfigDict(from_attributes=True)


class UserReadPrivate(UserReadPublic, ContactInfo):
    model_config = ConfigDict(from_attributes=True)
