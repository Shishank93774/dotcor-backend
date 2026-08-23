from typing import TYPE_CHECKING

from app.db.connection import Base

if TYPE_CHECKING:
    from app.db.models.message import Message
    from app.db.models.user import User
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import UniqueConstraint


class ChatRoom(Base):
    __tablename__ = "chat_rooms"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"), nullable=False)

    patient: Mapped["User"] = relationship(foreign_keys=[patient_id], back_populates="patient_chat_rooms")
    doctor: Mapped["User"] = relationship(foreign_keys=[doctor_id], back_populates="doctor_chat_rooms")

    messages: Mapped[list["Message"]] = relationship(back_populates="chat_room", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint(booking_id),)
