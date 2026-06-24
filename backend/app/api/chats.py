import json
import asyncio
import uuid
import html
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query, status
from sqlalchemy.orm import Session

from app.models.database import get_db, User, ChatSession, ChatMessage, WSTicket
from app.schemas.schemas import ChatSessionResponse, ChatMessageResponse
from app.api.auth import get_current_user

router = APIRouter(prefix="/chats", tags=["chats"])

from app.services.rag_service import RAGEngineService
rag_engine = RAGEngineService()

@router.post("/sessions", response_model=ChatSessionResponse)
def create_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = ChatSession(user_id=current_user.id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

@router.get("/sessions", response_model=List[ChatSessionResponse])
def get_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(ChatSession).filter(ChatSession.user_id == current_user.id).order_by(ChatSession.created_at.desc()).all()

@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
def get_session_messages(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    
    messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.timestamp.ascii if hasattr(ChatMessage.timestamp, "ascii") else ChatMessage.timestamp.asc()).all()
    
    response = []
    for msg in messages:
        sources_list = json.loads(msg.sources) if msg.sources else None
        response.append(
            ChatMessageResponse(
                id=msg.id,
                session_id=msg.session_id,
                role=msg.role,
                content=msg.content,
                timestamp=msg.timestamp,
                sources=sources_list
            )
        )
    return response

# WebSocket seguro
@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    ticket: str = Query(...),
    db: Session = Depends(get_db)
):
    # Validar ticket de un solo uso
    db_ticket = db.query(WSTicket).filter(WSTicket.id == ticket).first()
    if not db_ticket or db_ticket.expires_at < datetime.utcnow():
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Ticket inválido o expirado")
        return
    
    # Asociar conexión al usuario y borrar ticket
    user_id = db_ticket.user_id
    db.delete(db_ticket)
    db.commit()
    
    await websocket.accept()
    
    try:
        while True:
            # Esperar mensajes del cliente
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                session_id = payload.get("session_id")
                query = payload.get("query")
                if query:
                    query = html.escape(query.strip())

                
                if not session_id or not query:
                    await websocket.send_json({
                        "message_id": str(uuid.uuid4()),
                        "user_query": query or "",
                        "ai_response": "Error: Los parámetros session_id y query son obligatorios.",
                        "status": "error",
                        "error_detail": "Missing session_id or query",
                        "sources": []
                    })
                    continue
                
                # Validar que la sesión pertenece al usuario
                session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user_id).first()
                if not session:
                    await websocket.send_json({
                        "message_id": str(uuid.uuid4()),
                        "user_query": query,
                        "ai_response": "Error: La sesión especificada no existe o no te pertenece.",
                        "status": "error",
                        "error_detail": "Session access denied",
                        "sources": []
                    })
                    continue
                
                # Guardar mensaje del usuario
                user_msg = ChatMessage(
                    session_id=session_id,
                    role="user",
                    content=query
                )
                db.add(user_msg)
                db.commit()
                
                # Recuperar historial (últimos 10 mensajes)
                history = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.timestamp.desc()).limit(10).all()
                history.reverse() # Orden cronológico
                chat_history = [{"role": m.role, "content": m.content} for m in history]

                message_id = str(uuid.uuid4())
                accumulated_text = ""
                sources = []

                # Streaming asíncrono desde el motor RAG
                async for chunk_data in rag_engine.stream_response(query, chat_history):
                    if chunk_data["type"] == "content_chunk":
                        accumulated_text += chunk_data["chunk"]
                        await websocket.send_json({
                            "message_id": message_id,
                            "user_query": query,
                            "ai_response": accumulated_text.strip(),
                            "status": "processing",
                            "error_detail": None,
                            "sources": []
                        })
                    elif chunk_data["type"] == "final_result":
                        sources = chunk_data.get("sources", [])
                        await websocket.send_json({
                            "message_id": message_id,
                            "user_query": query,
                            "ai_response": chunk_data.get("full_text", accumulated_text),
                            "status": "completed",
                            "error_detail": None,
                            "sources": sources
                        })

                # Guardar mensaje de la IA en la DB al finalizar
                ai_msg = ChatMessage(
                    id=message_id,
                    session_id=session_id,
                    role="assistant",
                    content=accumulated_text,
                    sources=json.dumps(sources) if sources else None
                )
                db.add(ai_msg)
                db.commit()
                
            except json.JSONDecodeError:
                await websocket.send_json({
                    "message_id": str(uuid.uuid4()),
                    "user_query": "",
                    "ai_response": "Error: Formato de mensaje JSON inválido.",
                    "status": "error",
                    "error_detail": "JSONDecodeError",
                    "sources": []
                })
    except WebSocketDisconnect:
        # Desconexión normal del cliente
        pass
    except Exception as e:
        # Manejo de fallos imprevistos
        try:
            await websocket.send_json({
                "message_id": str(uuid.uuid4()),
                "user_query": "",
                "ai_response": "Error interno del servidor en la pasarela WebSocket.",
                "status": "error",
                "error_detail": str(e),
                "sources": []
            })
        except:
            pass
