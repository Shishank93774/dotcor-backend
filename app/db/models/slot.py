from datetime import UTC, datetime
from typing import TYPE_CHECKING

from app.db.connection import Base

if TYPE_CHECKING:
    from app.db.models.booking import Booking
    from app.db.models.doctor import Doctor

from sqlalchemy import CheckConstraint, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Slot(Base):
    __tablename__ = "slots"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), nullable=False)
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_booked: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    doctor: Mapped["Doctor"] = relationship(back_populates="slots")
    booking: Mapped["Booking | None"] = relationship(
        back_populates="slot", cascade="all, delete-orphan", uselist=False
    )

    __table_args__ = (
        CheckConstraint("start_time < end_time", name="ck_slot_valid_range"),
        ExcludeConstraint(
            (func.tstzrange(start_time, end_time, "[)"), "&&"),
            (doctor_id, "="),
            using="gist",
            name="ex_no_overlapping_slots_per_doctor",
        ),
    )
