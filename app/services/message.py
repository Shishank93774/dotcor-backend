from app.db.models.message import Message, MessageType
from app.services.ws_manager import ws_manager
from sqlalchemy import select
from sqlalchemy.orm import Session


class MessageService:
    def __init__(self, db: Session):
        self._db = db

    def save_message(self, sender_id: int, room_id: int, type: str, content: str) -> None:
        message = Message(sender_id=sender_id, room_id=room_id, type=type, content=content)
        self._db.add(message)
        self._db.commit()
        self._db.refresh(message)

        return None

    def get_messages_by_booking_id(self, room_id: int, offset: int = 0, limit: int = 25) -> list[Message]:
        messages = self._db.scalars(
            select(Message).where(Message.room_id == room_id).order_by(Message.created_at.desc()).offset(offset).limit(limit)
        ).all()
        return messages

    async def process_message(self, sender_id: int, room_id: int, content: str) -> None:
        if len(content) > 256:
            from app.core.exceptions import InvalidInputError
            raise InvalidInputError("Message too long")

        self.save_message(sender_id=sender_id, room_id=room_id, type=MessageType.TEXT, content=content)
        await ws_manager.broadcast(client_id=sender_id, room_id=room_id, message=content)
