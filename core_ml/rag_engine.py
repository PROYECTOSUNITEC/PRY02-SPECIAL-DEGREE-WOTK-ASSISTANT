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
    "1) Responde ÚNICAMENTE basándote en los fragmentos de contexto proporcionados. "
    "2) Está absolutamente prohibido inventar o alucinar citas bibliográficas, "
    "autores o libros; limítate a las fuentes reales del texto. "
    "3) Si la respuesta no está en el contexto, indica que no tienes la información. "
    "4) Usa formato Markdown."
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

    def _build_context(self, nodes) -> str:
        # construir contexto
        parts = []
        for i, node in enumerate(nodes, 1):
            meta = node.node.metadata
            headers = meta.get("jerarquia_headers", {})
            titulo = " > ".join(v for k, v in sorted(headers.items()) if v)
            parts.append(f"[fragmento {i}] {titulo}\n{node.node.text}")
        return "\n\n".join(parts) if parts else "(sin contexto disponible)"

    def ask_question(self, user_query: str):
        # recuperar y generar

        # paso 1: retrieval
        retriever = self._index.as_retriever(similarity_top_k=3)
        nodes = retriever.retrieve(user_query)

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
            return self._carousel.generate(SYSTEM_PROMPT, context, user_query)

        try:
            llm_response = _generate()
            logger.info("respuesta via %s [modelo: %s]", llm_response.provider, llm_response.model)

            def response_gen():
                yield llm_response.text

            return StreamingResponse(
                response_gen=response_gen(),
                source_nodes=nodes,
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
            )
