from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING

from app.db.connection import Base
from app.db.models.user import User

if TYPE_CHECKING:
    from app.db.models.chat_room import ChatRoom
from sqlalchemy import DateTime, ForeignKey
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship


class MessageType(str, Enum):
    TEXT = "text"
    DOCUMENT = "document"


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("chat_rooms.id"), nullable=False, index=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    type: Mapped[MessageType] = mapped_column(SAEnum(MessageType, values_callable=lambda enum: [e.value for e in enum]))
    content: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    chat_room: Mapped["ChatRoom"] = relationship(back_populates="messages")
    sender: Mapped["User"] = relationship()
