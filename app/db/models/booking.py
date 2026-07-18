from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING

from app.db.connection import Base

if TYPE_CHECKING:
    from app.db.models.patient import Patient
    from app.db.models.slot import Slot
from sqlalchemy import DateTime, ForeignKey
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Status(Enum):
    AVAILABLE = "available"
    BOOKED = "booked"
    CANCELLED = "cancelled"


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    slot_id: Mapped[int] = mapped_column(
        ForeignKey("slots.id"), unique=True, nullable=False
    )
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False)
    status: Mapped[Status] = mapped_column(SAEnum(Status))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    slot: Mapped["Slot"] = relationship(back_populates="booking")
    patient: Mapped["Patient"] = relationship(back_populates="bookings")
