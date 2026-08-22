from datetime import UTC, datetime
from typing import TYPE_CHECKING

from app.db.connection import Base

if TYPE_CHECKING:
    from app.db.models.auth import Auth
    from app.db.models.chat_room import ChatRoom
from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    role: Mapped[str]
    username: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(nullable=False)
    contact_number: Mapped[str] = mapped_column(unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    auth: Mapped["Auth"] = relationship(back_populates="user")
    patient_chat_rooms: Mapped[list["ChatRoom"]] = relationship(foreign_keys="[ChatRoom.patient_id]", back_populates="patient")
    doctor_chat_rooms: Mapped[list["ChatRoom"]] = relationship(foreign_keys="[ChatRoom.doctor_id]", back_populates="doctor")

    __mapper_args__ = {
        "polymorphic_identity": "users",
        "polymorphic_on": "role",
    }
