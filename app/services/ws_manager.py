from app.core.logging import get_logger
from fastapi import WebSocket

logger = get_logger(__name__)


class WebsocketManager:
    def __init__(self, room_id: int, patient_id: int, doctor_id: int):
        self._room_id = room_id
        self._patient_id = patient_id
        self._doctor_id = doctor_id
        self._patient_ws = None
        self._doctor_ws = None

    def _role_of(self, client_id: int) -> str:
        return "patient" if client_id == self._patient_id else "doctor"

    def _get_other_details(self, client_id: int) -> tuple[int, WebSocket]:
        if client_id == self._patient_id:
            return self._doctor_id, self._doctor_ws
        else:
            return self._patient_id, self._patient_ws

    async def _try_send_message(self, target_id: int, websocket: WebSocket, payload: dict) -> None:
        if not websocket:
            logger.info(f"Room {self._room_id}: no active socket for target {target_id}; dropped frame type={payload.get('type')} (peer offline)")
            return
        try:
            await websocket.send_json(payload)
        except Exception as e:
            logger.error(f"Room {self._room_id}: delivery FAILED to target {target_id}: {type(e).__name__}: {e}; forcing disconnect", exc_info=True)
            await self.disconnect(client_id=target_id, websocket=websocket)
        else:
            logger.info(f"Room {self._room_id}: delivered '{payload.get('type')}' frame to target {target_id}")

    async def reply_sender(self, client_id: int, payload: dict) -> None:
        websocket = self._patient_ws if client_id == self._patient_id else self._doctor_ws
        await self._try_send_message(
            target_id=client_id,
            websocket=websocket,
            payload=payload,
        )

    async def notify_other(self, client_id: int, behaviour: str) -> None:
        other_id, other_ws = self._get_other_details(client_id)

        logger.info(f"Room {self._room_id}: notifying other party about '{behaviour}' of {self._role_of(client_id)} {client_id}")

        await self._try_send_message(
            target_id=other_id,
            websocket=other_ws,
            payload={
                "sender_id": client_id,
                "type": "behaviour",
                "behaviour": behaviour,
            },
        )

    async def connect(self, client_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        if client_id == self._patient_id:
            self._patient_ws = websocket
        else:
            self._doctor_ws = websocket
        logger.info(f"Room {self._room_id}: {self._role_of(client_id)} {client_id} socket accepted and registered")

        await self.notify_other(client_id=client_id, behaviour="presence")

    async def disconnect(self, client_id: int, websocket: WebSocket | None) -> None:
        role = self._role_of(client_id)
        logger.info(f"Room {self._room_id}: disconnecting {role} {client_id}")
        if websocket is not None:
            try:
                await websocket.close()
            except Exception as e:
                logger.warning(f"Room {self._room_id}: close() failed for {role} {client_id} (socket likely already dead): {type(e).__name__}: {e}")
        else:
            logger.info(f"Room {self._room_id}: {role} {client_id} had no active socket; nothing to close")
        if self._patient_id == client_id:
            self._patient_ws = None
            await self.notify_other(client_id=self._patient_id, behaviour="absence")
        elif self._doctor_id == client_id:
            self._doctor_ws = None
            await self.notify_other(client_id=self._doctor_id, behaviour="absence")

    async def send_message(self, client_id: int, message: str) -> None:
        other_id, other_ws = self._get_other_details(client_id)
        logger.info(f"Room {self._room_id}: routing message from {self._role_of(client_id)} {client_id} to {other_id} ({len(message)} chars)")

        await self._try_send_message(
            target_id=other_id,
            websocket=other_ws,
            payload={
                "sender_id": client_id,
                "type": "message",
                "message": message,
            },
        )

    async def delete(self) -> None:
        logger.info(f"Deleting room {self._room_id}: closing both sockets")
        await self.disconnect(client_id=self._patient_id, websocket=self._patient_ws)
        await self.disconnect(client_id=self._doctor_id, websocket=self._doctor_ws)


class WebsocketRegistry:
    def __init__(self):
        self._managers: dict[int, WebsocketManager] = {}

    def get_or_create(self, room_id: int, patient_id: int, doctor_id: int) -> WebsocketManager:
        manager = self._managers.get(room_id)
        if manager is None:
            manager = WebsocketManager(room_id=room_id, patient_id=patient_id, doctor_id=doctor_id)
            self._managers[room_id] = manager
        return manager

    def remove(self, room_id: int) -> None:
        self._managers.pop(room_id, None)


websocket_registry = WebsocketRegistry()
