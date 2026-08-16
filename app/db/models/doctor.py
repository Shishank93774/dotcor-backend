from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.db.models.slot import Slot
from app.db.models.user import User
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Doctor(User):
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True, index=True)
    specialization: Mapped[str] = mapped_column(nullable=False)

    slots: Mapped[list["Slot"]] = relationship(back_populates="doctor", cascade="all, delete-orphan")

    __mapper_args__ = {"polymorphic_identity": "doctor"}

    def __repr__(self):
        return f"<Doctor(id={self.id}, username='{self.username}', specialization='{self.specialization}')>"
