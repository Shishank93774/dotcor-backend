from typing import TYPE_CHECKING

from app.db.models.chat_room import ChatRoom
from app.db.models.user import User

if TYPE_CHECKING:
    from app.db.models.booking import Booking
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Patient(User):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True, index=True)

    @property
    def chat_rooms(self) -> list["ChatRoom"]:
        return self.patient_chat_rooms

    bookings: Mapped[list["Booking"]] = relationship(back_populates="patient", cascade="all, delete-orphan")

    __mapper_args__ = {"polymorphic_identity": "patient"}

    def __repr__(self):
        return f"<Patient(id={self.id}, username='{self.username}')>"
