from datetime import UTC, datetime

from app.db.connection import Base
from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column


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

    __mapper_args__ = {
        "polymorphic_identity": "users",
        "polymorphic_on": "role",
    }
