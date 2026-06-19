import os
import logging
from pathlib import Path

from dotenv import load_dotenv

from llama_index.core import (
    Settings,
    StorageContext,
    load_index_from_storage,
)
from llama_index.core.base.response.schema import StreamingResponse
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

from core_ml.llm_fallback import LLMFallbackCarousel

logger = logging.getLogger(__name__)

# system prompt
SYSTEM_PROMPT = (
    "Eres el asistente académico institucional de la UNITEC para el "
    "Manual de Trabajo Especial de Grado. "
    "REGLAS: "
    "1) Responde ÚNICAMENTE basándote en el contexto de los documentos fuente provistos. "
    "2) Está absolutamente prohibido inventar o alucinar citas bibliográficas, "
    "autores o libros; limítate a las fuentes reales del texto. "
    "3) Si la respuesta no está en el contexto, indica que no tienes la información. "
    "4) Menciona la sección del manual y el número de página de forma natural en tu redacción (ej: 'Según la sección X (pág. Y)...'). "
    "NUNCA uses términos técnicos o internos del sistema como 'fragmento 1', 'nodo 1' o similares. "
    "5) Usa formato Markdown."
)

# prompt para normalizar consulta
QUERY_REWRITE_PROMPT = (
    "Corrige la ortografía, abreviaturas y errores tipográficos de la consulta de un estudiante sobre el Manual de Trabajo Especial de Grado. "
    "Ejemplos:\n"
    "- 'cm es el intrrlinead0 prs ls tes1s' -> '¿Cómo es el interlineado para la tesis?'\n"
    "- 'requisitos obligatorios teg' -> '¿Cuáles son los requisitos obligatorios para presentar el Trabajo Especial de Grado (TEG)?'\n"
    "- 'donde pongo los apendices' -> '¿Dónde se deben colocar los apéndices?'\n\n"
    "Consulta del estudiante: {query}\n"
    "Consulta corregida:"
)


_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_PERSIST_DIR = _PROJECT_ROOT / "data" / "vector_db"


class RAGQueryEngine:
    # motor rag con carrusel

    def __init__(self, persist_dir: str | Path | None = None) -> None:
        load_dotenv()

        # embeddings en cpu
        logger.info("Cargando modelo de embeddings BAAI/bge-m3 en CPU...")
        Settings.embed_model = HuggingFaceEmbedding(
            model_name="BAAI/bge-m3",
            device="cpu",
        )

        # carrusel multi-api
        logger.info("Inicializando carrusel LLM...")
        self._carousel = LLMFallbackCarousel()
        logger.info("Proveedores disponibles: %s", self._carousel.available_providers)

        # cargar indice
        resolved_dir = Path(persist_dir) if persist_dir else _DEFAULT_PERSIST_DIR
        if not resolved_dir.exists():
            raise FileNotFoundError(
                f"No se encontró el directorio del índice vectorial: {resolved_dir}."
            )

        logger.info("Cargando índice vectorial desde: %s", resolved_dir)
        storage_context = StorageContext.from_defaults(
            persist_dir=str(resolved_dir),
        )
        self._index = load_index_from_storage(storage_context)
        logger.info("RAGQueryEngine inicializado correctamente.")

    def _extraer_pagina(self, metadata: dict) -> int:
        # extraer nro de pagina
        paginas_origen = metadata.get("paginas_origen", [])
        if not paginas_origen:
            return 0
        nombre_archivo = paginas_origen[0].get("archivo", "")
        try:
            return int(nombre_archivo.split("_")[1].split(".")[0])
        except (IndexError, ValueError):
            return 0

    def _rewrite_query(self, user_query: str) -> str:
        # corregir errores ortograficos y abreviaturas
        try:
            prompt = QUERY_REWRITE_PROMPT.format(query=user_query)
            llm_response = self._carousel.generate(
                system_prompt="Eres un corrector ortográfico y normalizador de texto especializado en el ámbito académico.",
                context="",
                user_query=prompt
            )
            cleaned = llm_response.text.strip().strip('"').strip("'")
            logger.info("Consulta corregida de: '%s' a: '%s'", user_query, cleaned)
            return cleaned
        except Exception as e:
            logger.warning("No se pudo corregir la consulta ('%s'): %s. Usando original.", user_query, e)
            return user_query

    def _format_titulo(self, headers: dict) -> str:
        # formatear titulo de seccion
        if not headers:
            return "Sección General"
        if "header_path" in headers:
            path = headers["header_path"]
            parts = [p.strip() for p in path.split("/") if p.strip()]
            if parts:
                return " > ".join(parts)
        parts = []
        for key in ("Header_1", "Header_2", "Header_3"):
            val = headers.get(key)
            if val:
                parts.append(val)
        return " > ".join(parts) if parts else "Sección General"

    def _build_context(self, nodes) -> str:
        # construir contexto
        parts = []
        for node in nodes:
            meta = node.node.metadata
            headers = meta.get("jerarquia_headers", {})
            titulo = self._format_titulo(headers)
            pagina = self._extraer_pagina(meta)
            parts.append(f"Sección: {titulo} (Página {pagina})\nContenido:\n{node.node.text}")
        return "\n\n".join(parts) if parts else "(sin contexto disponible)"


    def ask_question(self, user_query: str, model_selection: str | None = None):
        # recuperar y generar

        # paso 0: normalizar consulta
        rewritten_query = self._rewrite_query(user_query)

        # paso 1: retrieval
        retriever = self._index.as_retriever(similarity_top_k=3)
        nodes = retriever.retrieve(rewritten_query)

        # paso 2: contexto
        context = self._build_context(nodes)

        # paso 3: generar
        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception(lambda e: "429" in str(e) or "quota" in str(e).lower()),
            reraise=True,
        )
        def _generate():
            return self._carousel.generate(SYSTEM_PROMPT, context, rewritten_query, provider_name=model_selection)

        try:
            llm_response = _generate()
            logger.info("respuesta via %s [modelo: %s]", llm_response.provider, llm_response.model)

            def response_gen():
                yield llm_response.text

            return StreamingResponse(
                response_gen=response_gen(),
                source_nodes=nodes,
                metadata={
                    "provider": llm_response.provider,
                    "model": llm_response.model,
                },
            )

        except Exception as e:
            logger.error("error en carrusel tras reintentos: %s", e)
            error_msg = f"Error al procesar la consulta: {str(e)}"
            if "429" in str(e) or "quota" in str(e).lower():
                error_msg = "Error: Alto volumen de consultas en todos los proveedores. Intenta de nuevo en unos segundos."

            def error_gen():
                yield error_msg

            return StreamingResponse(
                response_gen=error_gen(),
                source_nodes=[],
                metadata={
                    "provider": "error",
                    "model": "none",
                },
            )
