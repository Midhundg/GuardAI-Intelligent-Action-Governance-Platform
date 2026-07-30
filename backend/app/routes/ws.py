import asyncio
from typing import List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import structlog

logger = structlog.get_logger()

router = APIRouter(
    prefix="/ws",
    tags=["WebSockets"],
)


class ConnectionManager:
    """WebSocket Connection Manager for real-time live events."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("WebSocket client connected", total_clients=len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info("WebSocket client disconnected", total_clients=len(self.active_connections))

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)


ws_manager = ConnectionManager()


@router.websocket("")
@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        # Send initial welcome event
        await websocket.send_json({
            "event": "connected",
            "message": "Connected to GuardAI Enterprise Live Stream",
        })
        while True:
            # Echo heartbeat ping/pong
            data = await websocket.receive_text()
            await websocket.send_json({
                "event": "pong",
                "received": data,
            })
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning("WebSocket error", error=str(e))
        ws_manager.disconnect(websocket)
