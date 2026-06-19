from uuid import uuid4
from pydantic import BaseModel, Field

# request
class ChatRequest(BaseModel):
    session_id: str = Field(..., description="uuid de sesion")
    user_id: str = Field(..., description="uuid de usuario")
    query: str = Field(..., min_length=1, description="consulta del usuario")
    model_selection: str | None = Field(default=None, description="modelo seleccionado: auto | groq | cohere | gemini")


# referencia de fuente
class SourceReference(BaseModel):
    titulo_seccion: str = Field(..., description="titulo de seccion")
    numero_pagina: int = Field(..., description="pagina del manual")
    snippet: str = Field(..., description="texto citado")

# respuesta
class ChatResponse(BaseModel):
    message_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="uuid de respuesta",
    )
    user_query: str = Field(..., description="consulta original")
    ai_response: str = Field(default="", description="respuesta de la ia")
    status: str = Field(
        default="processing",
        description="processing | completed | error",
    )
    error_detail: str | None = Field(
        default=None,
        description="detalle del error",
    )
    sources: list[SourceReference] = Field(
        default_factory=list,
        description="fuentes recuperadas",
    )
    provider: str | None = Field(default=None, description="proveedor llm que respondio")
    model: str | None = Field(default=None, description="modelo llm que respondio")

