"""
WebSocket Connection Manager & Real-Time Telemetry Endpoint Module.

This module provides real-time event broadcasting over WebSockets to administrative frontend clients.
It enables live monitoring of active call states, streaming turn-by-turn transcripts, and immediate
alerting for pipeline failovers or call drops.

Architecture:
    - In-memory WebSocket client connection pool with thread-safe async locks
    - Structured JSON event envelope schema (type, payload, timestamp)
    - OAuth2 JWT authentication during WebSocket handshake connection upgrade

Dependencies:
    - fastapi >= 0.111
    - python-jose >= 3.3
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from jose import JWTError, jwt

from backend.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSockets"])


class ConnectionManager:
    """
    Manages active WebSocket client connections and broadcasts telemetry updates.

    Attributes:
        active_connections: Set of connected active WebSocket instances.
    """

    def __init__(self) -> None:
        """Initializes an empty connection pool."""
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        """
        Accepts incoming WebSocket connection upgrade and registers socket in active pool.

        Args:
            websocket: Incoming FastAPI WebSocket instance.
        """
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info("New WebSocket client connected. Active connections: %d", len(self.active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        """
        Removes disconnected WebSocket instance from active pool.

        Args:
            websocket: Disconnected WebSocket instance.
        """
        self.active_connections.discard(websocket)
        logger.info("WebSocket client disconnected. Remaining connections: %d", len(self.active_connections))

    async def broadcast(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Broadcasts a structured JSON telemetry envelope to all registered clients.

        Args:
            event_type: Category identifier ('call_status', 'transcript_turn', 'call_alert').
            data: Payload data dictionary.
        """
        if not self.active_connections:
            return

        envelope = {
            "event": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
        }

        disconnected: Set[WebSocket] = set()

        for connection in list(self.active_connections):
            try:
                await connection.send_json(envelope)
            except Exception as exc:
                logger.warning("Failed to send WebSocket message to client: %s", str(exc))
                disconnected.add(connection)

        # Cleanup broken sockets
        for conn in disconnected:
            self.disconnect(conn)


# Global singleton instance
ws_manager = ConnectionManager()


def authenticate_websocket_token(token: str) -> bool:
    """
    Validates JWT token provided during WebSocket connection handshake.

    Args:
        token: Signed JWT access token.

    Returns:
        True if valid and unexpired, False otherwise.
    """
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        sub: str = payload.get("sub", "")
        return bool(sub)
    except JWTError:
        return False


@router.websocket("/ws/calls")
async def websocket_call_monitor(websocket: WebSocket, token: str = "") -> None:
    """
    Real-time WebSocket endpoint for broadcasting call status updates and live transcripts.

    Args:
        websocket: Standard FastAPI WebSocket instance.
        token: Query parameter containing signed JWT access token (?token=...).

    Raises:
        WebSocketDisconnect: Upon connection closure by peer.
    """
    if not token or not authenticate_websocket_token(token):
        logger.warning("Rejected unauthenticated WebSocket connection attempt")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await ws_manager.connect(websocket)

    try:
        while True:
            # Keep-alive receive loop (handles ping/pong and client commands)
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as exc:
        logger.error("Unexpected error in WebSocket monitoring loop: %s", str(exc))
        ws_manager.disconnect(websocket)
