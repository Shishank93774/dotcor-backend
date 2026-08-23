from app.core.exceptions import InvalidInputError, InvalidTokenError, ResourceNotFoundError, UnauthorizedError
from app.core.logging import get_logger
from app.core.services import get_auth_service, get_booking_service, get_chat_room_service
from app.schemas.booking import BookingCreate, BookingRead
from app.schemas.message import MessageRead
from app.services.auth import AuthService
from app.services.booking import BookingService
from app.services.chat_room import ChatRoomService
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, WebSocketException, status

router = APIRouter(prefix="/bookings", tags=["bookings"])

logger = get_logger(__name__)


@router.post("/", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
def create_booking(booking: BookingCreate, booking_service: BookingService = Depends(get_booking_service)):
    return booking_service.create_booking(**booking.model_dump())


@router.get("/{booking_id}", response_model=BookingRead, status_code=status.HTTP_200_OK)
def get_booking(booking_id: int, booking_service: BookingService = Depends(get_booking_service)):
    return booking_service.get_booking(booking_id)


@router.get("/", response_model=list[BookingRead], status_code=status.HTTP_200_OK)
def get_bookings(booking_service: BookingService = Depends(get_booking_service)):
    return booking_service.list_bookings()


@router.patch("/cancel", response_model=BookingRead, status_code=status.HTTP_200_OK)
def cancel_booking(booking_id: int, booking_service: BookingService = Depends(get_booking_service)):
    return booking_service.cancel_booking(booking_id)


@router.delete("/{booking_id}", response_model=None, status_code=status.HTTP_204_NO_CONTENT)
def delete_booking(booking_id: int, booking_service: BookingService = Depends(get_booking_service)):
    return booking_service.delete_booking(booking_id)


@router.get("/{booking_id}/messages", response_model=list[MessageRead], status_code=status.HTTP_200_OK)
def get_messages(
    booking_id: int,
    token: str = Query(...),
    offset: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
    booking_service: BookingService = Depends(get_booking_service),
    auth_service: AuthService = Depends(get_auth_service),
    chat_room_service: ChatRoomService = Depends(get_chat_room_service),
):
    auth = auth_service.verify(token)
    logger.info(f"History request: user {auth.user_id} reading messages of booking {booking_id} (offset={offset}, limit={limit})")

    try:
        booking_service.verify_chat_access(user_id=auth.user_id, booking_id=booking_id)
    except (ResourceNotFoundError, UnauthorizedError):
        logger.warning(f"History denied: user {auth.user_id} may not read booking {booking_id}")
        raise UnauthorizedError("Booking not found or unauthorized")

    chat_room = chat_room_service.get_chat_room_by_booking_id(booking_id)
    return chat_room_service.load_messages(room_id=chat_room.id, offset=offset, limit=limit)


@router.websocket("/{booking_id}/ws")
async def chat(
    booking_id: int,
    websocket: WebSocket,
    token: str = Query(...),
    booking_service: BookingService = Depends(get_booking_service),
    auth_service: AuthService = Depends(get_auth_service),
    chat_room_service: ChatRoomService = Depends(get_chat_room_service),
):
    logger.info(f"WS handshake started for booking {booking_id}")
    try:
        auth = auth_service.verify(token)
    except InvalidTokenError:
        logger.warning(f"WS auth rejected for booking {booking_id}: invalid or expired token")
        raise WebSocketException(code=status.WS_1007_INVALID_FRAME_PAYLOAD_DATA, reason="Failed to Authenticate")

    user_id = auth.user_id
    logger.info(f"WS handshake authenticated user {user_id} for booking {booking_id}")

    try:
        booking = booking_service.verify_chat_access(user_id, booking_id)
    except (ResourceNotFoundError, UnauthorizedError):
        logger.warning(f"WS access denied: user {user_id} on booking {booking_id} (not a participant or booking not active)")
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Booking not found or unauthorized")

    chat_room = chat_room_service.create_chat_room(patient_id=booking.patient_id, doctor_id=booking.slot.doctor_id, booking_id=booking_id)

    await chat_room_service.connect(client_id=user_id, websocket=websocket)
    logger.info(f"WS session established: user {user_id} in room {chat_room.id} (booking {booking_id})")

    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"Room {chat_room.id}: received message from user {user_id} ({len(data)} chars)")

            await chat_room_service.send_message(
                sender_id=user_id,
                room_id=chat_room.id,
                content=data,
            )
    except WebSocketDisconnect:
        logger.info(f"WS session ended normally: user {user_id} left room {chat_room.id} (booking {booking_id})")
        await chat_room_service.disconnect(client_id=user_id, websocket=websocket)
    except Exception:
        logger.exception(f"WS session CRASHED: user {user_id}, room {chat_room.id}, booking {booking_id} - see traceback below")
        raise
