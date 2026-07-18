from app.db.models.booking import Booking
from app.db.models.user import User
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Patient(User):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)

    bookings: Mapped[list["Booking"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )

    __mapper_args__ = {"polymorphic_identity": "patient"}

    def __repr__(self):
        return f"<Patient(id={self.id}, username='{self.username}')>"
