from app.core.exceptions import InvalidInputError
from app.core.logging import get_logger
from app.db.models.message import Message
from sqlalchemy import select
from sqlalchemy.orm import Session

logger = get_logger(__name__)

MAX_MESSAGE_LENGTH = 256


class MessageService:
    def __init__(self, db: Session):
        self._db = db

    def _save_message(self, sender_id: int, room_id: int, type: str, content: str) -> Message:
        message = Message(sender_id=sender_id, room_id=room_id, type=type, content=content)
        self._db.add(message)
        self._db.commit()
        self._db.refresh(message)

        return message

    def process_message(self, sender_id: int, room_id: int, type: str, content: str) -> None:
        if len(content) > MAX_MESSAGE_LENGTH:
            logger.warning(f"Message rejected from sender {sender_id} in room {room_id}: {len(content)} chars exceeds limit {MAX_MESSAGE_LENGTH}")
            raise InvalidInputError(
                f"Message too long ({len(content)} > {MAX_MESSAGE_LENGTH})",
                detail={"code": "message_too_long", "limit": MAX_MESSAGE_LENGTH, "received_length": len(content)},
            )
        # TODO: Add other content validations

        message = self._save_message(sender_id=sender_id, room_id=room_id, type=type, content=content)
        logger.info(f"Message persisted: id={message.id} room={room_id} sender={sender_id} type={type} length={len(content)}")

    def load_messages(self, room_id: int, offset: int = 0, limit: int = 10) -> list[Message]:
        messages = self._db.scalars(
            select(Message).where(Message.room_id == room_id).order_by(Message.created_at.desc()).offset(offset).limit(limit)
        ).all()
        logger.info(f"History read: {len(messages)} messages for room {room_id} (offset={offset}, limit={limit})")
        return messages
