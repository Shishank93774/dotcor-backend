from app.core.exceptions import InvalidInputError, ResourceNotFoundError
from app.core.logging import get_logger
from app.db.models.booking import Booking
from app.db.models.chat_room import ChatRoom
from app.db.models.message import Message, MessageType
from app.services.message import MessageService
from app.services.ws_manager import websocket_registry
from fastapi import WebSocket
from sqlalchemy import select
from sqlalchemy.orm import Session

logger = get_logger(__name__)


class ChatRoomService:
    def __init__(self, db: Session):
        self._db = db
        self._ws_manager = None

    def get_chat_room(self, room_id: int) -> ChatRoom:
        chat_room = self._db.scalars(select(ChatRoom).where(ChatRoom.id == room_id)).first()
        if not chat_room:
            logger.warning(f"Chat room with ID {room_id} not found")
            raise ResourceNotFoundError("Chat room not found")
        logger.info(f"Retrieved chat room ID: {room_id}")
        return chat_room

    def get_chat_room_by_booking_id(self, booking_id: int) -> ChatRoom:
        chat_room = self._db.scalars(select(ChatRoom).where(ChatRoom.booking_id == booking_id)).first()
        if not chat_room:
            logger.warning(f"Chat room with booking ID {booking_id} not found")
            raise ResourceNotFoundError("Chat room not found")
        logger.info(f"Retrieved chat room by booking ID: {booking_id}")
        return chat_room

    def create_chat_room(self, patient_id: int, doctor_id: int, booking_id: int) -> ChatRoom:
        try:
            chat_room = self.get_chat_room_by_booking_id(booking_id=booking_id)
        except ResourceNotFoundError:
            chat_room = None
        if chat_room:
            logger.info(f"Fast path: chat room {chat_room.id} already exists for booking {booking_id}; reusing (no lock taken)")
            self._ws_manager = websocket_registry.get_or_create(room_id=chat_room.id, patient_id=patient_id, doctor_id=doctor_id)
            logger.info(f"Registry: manager resolved for chat room {chat_room.id}")
            return chat_room

        logger.info(f"Slow path: no existing chat room for booking {booking_id}; acquiring lock")

        # Hold booking to try creating chat
        booking = self._db.scalars(select(Booking).where(Booking.id == booking_id).with_for_update()).first()
        if not booking:
            logger.warning(f"Booking with ID {booking_id} not found while holding lock")
            raise ResourceNotFoundError("Booking not found")

        logger.info(f"Lock acquired on booking {booking_id}; re-checking room existence inside lock window")
        try:
            chat_room = self.get_chat_room_by_booking_id(booking_id=booking_id)
        except ResourceNotFoundError:
            chat_room = None

        if chat_room is None:
            chat_room = ChatRoom(patient_id=patient_id, doctor_id=doctor_id, booking_id=booking.id)
            self._db.add(chat_room)
            self._db.commit()
            self._db.refresh(chat_room)
            logger.info(f"Won race: created chat room {chat_room.id} for booking {booking_id}")
        else:
            logger.info(f"Lost race: chat room {chat_room.id} for booking {booking_id} was created concurrently; reusing")
            self._db.commit()

        self._ws_manager = websocket_registry.get_or_create(room_id=chat_room.id, patient_id=patient_id, doctor_id=doctor_id)
        logger.info(f"Registry: manager resolved for chat room {chat_room.id}")
        return chat_room

    async def connect(self, client_id: int, websocket: WebSocket) -> None:
        await self._ws_manager.connect(client_id=client_id, websocket=websocket)
        logger.info(f"Client {client_id} connected to room {self._ws_manager._room_id}")

        return None

    async def disconnect(self, client_id: int, websocket: WebSocket) -> None:
        await self._ws_manager.disconnect(client_id=client_id, websocket=websocket)
        logger.warning(f"Client {client_id} disconnected from room {self._ws_manager._room_id}")
        return None

    def load_messages(self, room_id: int, offset: int = 0, limit: int = 25) -> list[Message]:
        messages = MessageService(db=self._db).load_messages(room_id=room_id, offset=offset, limit=limit)
        logger.info(f"Loaded {len(messages)} messages for room ID: {room_id}")
        return messages

    async def send_message(self, sender_id: int, room_id: int, content: str) -> None:
        try:
            MessageService(db=self._db).process_message(sender_id=sender_id, room_id=room_id, type=MessageType.TEXT, content=content)
        except InvalidInputError as e:
            await self._ws_manager.reply_sender(
                client_id=sender_id,
                payload={"sender_id": sender_id, "type": "error", **(e.detail or {})},
            )
            return None

        await self._ws_manager.send_message(client_id=sender_id, message=content)

        return None

    async def delete_chat_room(self, room_id: int) -> None:
        chat_room = self.get_chat_room(room_id)
        self._db.delete(chat_room)
        await self._ws_manager.delete()
        websocket_registry.remove(room_id=room_id)
        self._db.commit()
        logger.info(f"Deleted chat room ID: {room_id}")

        return None
