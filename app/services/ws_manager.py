from app.core.logging import get_logger
from fastapi import WebSocket

logger = get_logger(__name__)


class WebsocketManager:
    def __init__(self):
        self.rooms: dict[int, set[WebSocket]] = {}
        self.connection_to_room_map: dict[WebSocket, int] = {}
        self.connection_to_client_map: dict[WebSocket, int] = {}

    async def connect(self, websocket: WebSocket, client_id: int, room_id: int):
        await websocket.accept()
        logger.info(f"Client {client_id} connected through {websocket.client} to room {room_id}")
        self.rooms[room_id] = self.rooms.get(room_id, set())
        self.rooms[room_id].add(websocket)
        self.connection_to_room_map[websocket] = room_id
        self.connection_to_client_map[websocket] = client_id

    async def disconnect(self, websocket: WebSocket):
        logger.info(f"Connection through {websocket.client} disconnected")
        room_id = self.connection_to_room_map[websocket]

        self.rooms[room_id].discard(websocket)
        if not self.rooms[room_id]:  # Clear rooms
            del self.rooms[room_id]

        self.connection_to_room_map.pop(websocket)
        self.connection_to_client_map.pop(websocket)

    async def broadcast(self, client_id: int, room_id: int, message: str):
        dead = []
        logger.info(f"Broadcasting to {len(self.rooms[room_id])} connections")
        for conn in self.rooms[room_id]:
            try:
                await conn.send_json({"sender": client_id, "message": message})
            except Exception:
                dead.append(conn)
        for conn in dead:
            await self.disconnect(conn)


ws_manager = WebsocketManager()
