import logging
from uuid import uuid4

from core_ml.rag_engine import RAGQueryEngine
from modules.chats.schemas import ChatResponse, SourceReference

logger = logging.getLogger(__name__)

# singleton rag
_engine: RAGQueryEngine | None = None


def _get_engine() -> RAGQueryEngine:
    # inicializacion lazy
    global _engine
    if _engine is None:
        logger.info("Inicializando RAGQueryEngine...")
        _engine = RAGQueryEngine()
    return _engine


def _extraer_pagina(metadata: dict) -> int:
    # extraer nro de pagina
    paginas_origen = metadata.get("paginas_origen", [])
    if not paginas_origen:
        return 0

    nombre_archivo = paginas_origen[0].get("archivo", "")
    try:
        return int(nombre_archivo.split("_")[1].split(".")[0])
    except (IndexError, ValueError):
        return 0


def _extraer_titulo_seccion(metadata: dict) -> str:
    # extraer titulo de seccion
    headers = metadata.get("jerarquia_headers", {})
    if not headers:
        return "Sección General"
    if "header_path" in headers:
        path = headers["header_path"]
        parts = [p.strip() for p in path.split("/") if p.strip()]
        if parts:
            return " > ".join(parts)
    partes = []
    for key in ("Header_1", "Header_2", "Header_3"):
        valor = headers.get(key)
        if valor:
            partes.append(valor)
    return " > ".join(partes) if partes else "Sección General"



async def procesar_consulta_rag(user_query: str, model_selection: str | None = None) -> ChatResponse:
    # procesar consulta contra rag
    message_id = str(uuid4())

    try:
        engine = _get_engine()
        response = engine.ask_question(user_query, model_selection=model_selection)

        # tokens del stream
        tokens: list[str] = []
        for token in response.response_gen:
            tokens.append(token)

        respuesta_completa = "".join(tokens)

        # extraer fuentes
        sources: list[SourceReference] = []
        if hasattr(response, "source_nodes"):
            for nodo in response.source_nodes:
                metadata = nodo.node.metadata
                sources.append(
                    SourceReference(
                        titulo_seccion=_extraer_titulo_seccion(metadata),
                        numero_pagina=_extraer_pagina(metadata),
                        snippet=nodo.node.text[:300],
                    )
                )

        # extraer metadatos de modelo/proveedor
        provider = "desconocido"
        model = "desconocido"
        if response.metadata:
            provider = response.metadata.get("provider", provider)
            model = response.metadata.get("model", model)

        return ChatResponse(
            message_id=message_id,
            user_query=user_query,
            ai_response=respuesta_completa,
            status="completed",
            sources=sources,
            provider=provider,
            model=model,
        )


    except Exception as e:
        logger.exception("Error procesando consulta RAG: %s", e)
        return ChatResponse(
            message_id=message_id,
            user_query=user_query,
            ai_response="",
            status="error",
            error_detail=str(e),
        )
