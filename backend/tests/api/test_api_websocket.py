"""
WebSocket & Real-Time Telemetry Tests — Handshake Authentication, Keepalive & Broadcasting.

Tests `backend.websocket.manager`:
- authenticate_websocket_token: Token validation, expiration, signature verification.
- ConnectionManager: Connection registration, safe cleanup, resilient parallel broadcasting.
- WebSocket endpoint /ws/calls: Policy violation 1008 rejection on unauthenticated attempts,
  ping/pong keepalive loop, live telemetry event reception.
"""

import datetime
from unittest.mock import AsyncMock, MagicMock
from fastapi import WebSocket
import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from backend.api.auth import create_jwt_token
from backend.main import app
from backend.websocket.manager import (
    ConnectionManager,
    authenticate_websocket_token,
    ws_manager,
)


# ------------------------------------------------------------------------------
# 1. Token Handshake Validator Tests
# ------------------------------------------------------------------------------
def test_authenticate_websocket_token_valid():
    """Verifies valid JWT token is accepted during WebSocket handshake."""
    token = create_jwt_token(
        data={"sub": "1", "role": "admin"},
        expires_delta=datetime.timedelta(minutes=15),
    )
    assert authenticate_websocket_token(token) is True


def test_authenticate_websocket_token_expired():
    """Verifies expired JWT token is rejected during WebSocket handshake."""
    token = create_jwt_token(
        data={"sub": "1", "role": "admin"},
        expires_delta=datetime.timedelta(minutes=-10),
    )
    assert authenticate_websocket_token(token) is False


def test_authenticate_websocket_token_missing_sub():
    """Verifies JWT token without subject claim is rejected."""
    token = create_jwt_token(
        data={"role": "admin"},
        expires_delta=datetime.timedelta(minutes=15),
    )
    assert authenticate_websocket_token(token) is False


def test_authenticate_websocket_token_tampered():
    """Verifies tampered token fails signature verification."""
    token = create_jwt_token(data={"sub": "1"}, expires_delta=datetime.timedelta(minutes=15))
    tampered = token[:-5] + "XXXXX"
    assert authenticate_websocket_token(tampered) is False


def test_authenticate_websocket_token_empty():
    """Verifies empty string is rejected."""
    assert authenticate_websocket_token("") is False


# ------------------------------------------------------------------------------
# 2. Connection Manager Unit Tests
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_connection_manager_connect_and_disconnect():
    """Verifies connect and disconnect register and deregister sockets."""
    manager = ConnectionManager()
    mock_ws = AsyncMock(spec=WebSocket)

    await manager.connect(mock_ws)
    assert mock_ws in manager.active_connections
    mock_ws.accept.assert_awaited_once()

    manager.disconnect(mock_ws)
    assert mock_ws not in manager.active_connections


@pytest.mark.asyncio
async def test_connection_manager_broadcast_empty():
    """Verifies broadcast with zero connections exits without exception."""
    manager = ConnectionManager()
    await manager.broadcast("call_status", {"status": "ok"})
    # Must not raise


@pytest.mark.asyncio
async def test_connection_manager_broadcast_active_clients():
    """Verifies broadcast sends structured envelope to all active clients."""
    manager = ConnectionManager()
    ws1 = AsyncMock(spec=WebSocket)
    ws2 = AsyncMock(spec=WebSocket)

    manager.active_connections.add(ws1)
    manager.active_connections.add(ws2)

    await manager.broadcast("call_status", {"task_id": 101, "status": "ringing"})

    assert ws1.send_json.await_count == 1
    call_args_1 = ws1.send_json.await_args[0][0]
    assert call_args_1["event"] == "call_status"
    assert call_args_1["data"]["task_id"] == 101
    assert "timestamp" in call_args_1

    assert ws2.send_json.await_count == 1


@pytest.mark.asyncio
async def test_connection_manager_broadcast_cleans_broken_sockets():
    """Verifies broken client sockets encountering network exceptions are automatically evicted."""
    manager = ConnectionManager()
    healthy_ws = AsyncMock(spec=WebSocket)
    broken_ws = AsyncMock(spec=WebSocket)
    broken_ws.send_json.side_effect = RuntimeError("Socket connection closed")

    manager.active_connections.add(healthy_ws)
    manager.active_connections.add(broken_ws)

    await manager.broadcast("test_event", {"val": 1})

    assert healthy_ws in manager.active_connections
    assert broken_ws not in manager.active_connections


# ------------------------------------------------------------------------------
# 3. WebSocket Endpoint Handshake & Integration Tests
# ------------------------------------------------------------------------------
def test_websocket_rejects_missing_token():
    """Verifies /ws/calls without token closes with code 1008 (Policy Violation)."""
    client = TestClient(app)
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect("/ws/calls"):
            pass
    assert exc_info.value.code == 1008


def test_websocket_rejects_invalid_token():
    """Verifies /ws/calls with corrupted token closes with code 1008."""
    client = TestClient(app)
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect("/ws/calls?token=invalid.jwt.token"):
            pass
    assert exc_info.value.code == 1008


def test_websocket_accepts_valid_token_and_ping_pong(admin_token: str):
    """Verifies authenticated WebSocket connection upgrade and ping-pong loop."""
    client = TestClient(app)
    with client.websocket_connect(f"/ws/calls?token={admin_token}") as ws:
        ws.send_text("ping")
        data = ws.receive_text()
        assert data == "pong"
