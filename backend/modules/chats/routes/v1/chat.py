import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chats", tags=["chats"])


@router.get("/")
async def get_chats():
    return {"message": "Hello, World!"}


@router.websocket("/ws")
async def chat_websocket(websocket: WebSocket) -> None:
    """Canal en tiempo real para mensajes de chat (eco hasta integrar el agente)."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(data)
    except WebSocketDisconnect:
        logger.debug("Cliente WebSocket desconectado")
