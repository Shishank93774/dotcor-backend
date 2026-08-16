from app.core.exceptions import InvalidTokenError, ResourceNotFoundError
from app.core.services import get_auth_service, get_booking_service, get_message_service
from app.db.models.message import MessageType
from app.schemas.booking import BookingCreate, BookingRead
from app.services.auth import AuthService
from app.services.booking import BookingService
from app.services.message import MessageService
from app.services.ws_manager import ws_manager
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, WebSocketException, status

router = APIRouter(prefix="/bookings", tags=["bookings"])


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


@router.get("/{booking_id}/messages")
def get_messages(
    booking_id: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(25, ge=1),
    message_service: MessageService = Depends(get_message_service),
):
    return message_service.get_messages_by_booking_id(room_id=booking_id, offset=offset, limit=limit)


@router.websocket("/{booking_id}/ws")
async def chat(
    booking_id: int,
    websocket: WebSocket,
    token: str = Query(...),
    booking_service: BookingService = Depends(get_booking_service),
    auth_service: AuthService = Depends(get_auth_service),
    message_service: MessageService = Depends(get_message_service),
):
    try:
        auth = auth_service.verify(token)
    except InvalidTokenError:
        raise WebSocketException(code=status.WS_1007_INVALID_FRAME_PAYLOAD_DATA, reason="Failed to Authenticate")

    try:
        booking = booking_service.get_booking(booking_id)
    except ResourceNotFoundError:
        raise WebSocketException(code=status.WS_1007_INVALID_FRAME_PAYLOAD_DATA, reason="Booking not found")

    if booking.status != "booked":
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Booking not found or is cancelled")

    user_id = auth.user_id

    if user_id not in (booking.patient_id, booking.slot.doctor_id):
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Failed to Authenticate")

    await ws_manager.connect(websocket=websocket, client_id=user_id, room_id=booking_id)
    try:
        while True:
            data = await websocket.receive_text()
            if len(data) > 256:
                raise WebSocketException(code=status.WS_1007_INVALID_FRAME_PAYLOAD_DATA, reason="Message too long")
            message_service.save_message(sender_id=user_id, room_id=booking_id, type=MessageType.TEXT, content=data)

            await ws_manager.broadcast(client_id=user_id, room_id=booking_id, message=data)
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket=websocket)
