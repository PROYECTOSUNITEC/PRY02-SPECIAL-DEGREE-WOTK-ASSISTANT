import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from modules.chats.schemas import ChatRequest, ChatResponse
from modules.chats.service import procesar_consulta_rag

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chats", tags=["chats"])


@router.get("/")
async def get_chats():
    return {"message": "Hello, World!"}


@router.websocket("/ws")
async def chat_websocket(websocket: WebSocket) -> None:
    """Canal en tiempo real para mensajes de chat (eco hasta integrar el agente)."""
    await websocket.accept()
    logger.info("Cliente WebSocket conectado")

    try:
        while True:
            raw = await websocket.receive_text()

            # validar payload
            try:
                payload = json.loads(raw)
                request = ChatRequest(**payload)
            except (json.JSONDecodeError, ValidationError) as e:
                error_response = ChatResponse(
                    user_query=raw[:200],
                    status="error",
                    error_detail=f"Payload inválido: {e}",
                )
                await websocket.send_text(
                    error_response.model_dump_json()
                )
                continue

            logger.info(
                "Consulta recibida [session=%s, user=%s]: %s",
                request.session_id,
                request.user_id,
                request.query[:80],
            )

            # notificar processing
            processing_response = ChatResponse(
                user_query=request.query,
                status="processing",
            )
            await websocket.send_text(
                processing_response.model_dump_json()
            )

            # procesar consulta
            response = await procesar_consulta_rag(request.query)
            await websocket.send_text(response.model_dump_json())

            logger.info(
                "Respuesta enviada [message_id=%s, status=%s, sources=%d]",
                response.message_id,
                response.status,
                len(response.sources),
            )

    except WebSocketDisconnect:
        logger.info("Cliente WebSocket desconectado")
