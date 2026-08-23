import asyncio

import pytest

from app.services.ws_manager import WebsocketManager, websocket_registry


class FakeWS:
    def __init__(self, fail_send=False, fail_close=False):
        self.inbox = []
        self.closed = False
        self.accepted = False
        self._fail_send = fail_send
        self._fail_close = fail_close

    async def accept(self):
        self.accepted = True

    async def send_json(self, payload):
        if self._fail_send:
            raise RuntimeError("send on dead socket")
        self.inbox.append(payload)

    async def close(self):
        if self._fail_close:
            raise RuntimeError("close on dead socket")
        self.closed = True


def _manager(room_id=1):
    return WebsocketManager(room_id=room_id, patient_id=10, doctor_id=20)


@pytest.mark.asyncio
async def test_reply_sender_routes_to_caller_socket():
    m = _manager()
    patient_ws, doctor_ws = FakeWS(), FakeWS()
    await m.connect(client_id=10, websocket=patient_ws)
    await m.connect(client_id=20, websocket=doctor_ws)
    patient_ws.inbox.clear()
    doctor_ws.inbox.clear()

    await m.reply_sender(client_id=10, payload={"type": "error", "code": "x"})
    assert patient_ws.inbox == [{"type": "error", "code": "x"}]
    assert doctor_ws.inbox == []

    await m.reply_sender(client_id=20, payload={"type": "error", "code": "y"})
    assert doctor_ws.inbox == [{"type": "error", "code": "y"}]
    assert len(patient_ws.inbox) == 1


@pytest.mark.asyncio
async def test_failed_delivery_forces_peer_disconnect_and_notifies_survivor():
    m = _manager()
    patient_ws = FakeWS()
    dead_doctor_ws = FakeWS(fail_send=True)
    await m.connect(client_id=10, websocket=patient_ws)
    await m.connect(client_id=20, websocket=dead_doctor_ws)
    patient_ws.inbox.clear()

    await m.send_message(client_id=10, message="into the void")

    assert dead_doctor_ws.inbox == []
    assert dead_doctor_ws.closed is True
    assert m._doctor_ws is None
    assert m._patient_ws is patient_ws
    assert patient_ws.inbox == [
        {"sender_id": 20, "type": "behaviour", "behaviour": "absence"}
    ]


@pytest.mark.asyncio
async def test_dual_dead_sockets_disconnect_terminates():
    m = _manager()
    p = FakeWS(fail_send=True, fail_close=True)
    d = FakeWS(fail_send=True, fail_close=True)
    m._patient_ws = p
    m._doctor_ws = d

    await asyncio.wait_for(m.disconnect(client_id=10, websocket=p), timeout=3)

    assert m._patient_ws is None
    assert m._doctor_ws is None


@pytest.mark.asyncio
async def test_delete_terminates_with_dead_sockets():
    m = _manager()
    p = FakeWS(fail_send=True, fail_close=True)
    d = FakeWS(fail_send=True, fail_close=True)
    m._patient_ws = p
    m._doctor_ws = d

    await asyncio.wait_for(m.delete(), timeout=3)

    assert m._patient_ws is None
    assert m._doctor_ws is None


@pytest.mark.asyncio
async def test_registry_same_room_same_instance_and_removal():
    a = websocket_registry.get_or_create(room_id=987654, patient_id=1, doctor_id=2)
    b = websocket_registry.get_or_create(room_id=987654, patient_id=1, doctor_id=2)
    assert a is b

    websocket_registry.remove(room_id=987654)
    c = websocket_registry.get_or_create(room_id=987654, patient_id=1, doctor_id=2)
    assert c is not a

    websocket_registry.remove(room_id=987654)
