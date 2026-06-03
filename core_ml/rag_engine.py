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
from llama_index.llms.gemini import Gemini

import google.generativeai as genai
from google.api_core.retry import Retry
import google.api_core.exceptions
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

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
    # motor rag con llamaindex + gemini + bge-m3

    def __init__(self, persist_dir: str | Path | None = None) -> None:
        # cargar variables de entorno
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "La variable de entorno GOOGLE_API_KEY no está configurada."
            )

        # modelo embeddings en cpu
        logger.info("Cargando modelo de embeddings BAAI/bge-m3 en CPU...")
        Settings.embed_model = HuggingFaceEmbedding(
            model_name="BAAI/bge-m3",
            device="cpu",
        )

        logger.info("Configurando LLM Gemini...")

        # retry policy para api google
        retry_policy = Retry(
            initial=1.0,
            maximum=10.0,
            multiplier=2.0,
            predicate=lambda e: isinstance(e, google.api_core.exceptions.GoogleAPICallError) and e.code == 429,
        )
        request_options = genai.types.RequestOptions(retry=retry_policy)

        Settings.llm = Gemini(
            model="models/gemini-flash-latest",
            temperature=0.1,
            system_prompt=SYSTEM_PROMPT,
            max_retries=5,
            request_options=request_options,
        )

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

    def ask_question(self, user_query: str):
        # ejecutar consulta contra el indice rag
        query_engine = self._index.as_query_engine(
            streaming=True,
            similarity_top_k=3,
        )

        # retry con tenacity para mitigacion de 429
        @retry(
            stop=stop_after_attempt(5),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception(lambda e: "429" in str(e) or "quota" in str(e).lower() or "limit" in str(e).lower()),
            reraise=True
        )
        def _execute_query_with_retry():
            return query_engine.query(user_query)

        try:
            response = _execute_query_with_retry()
            original_gen = response.response_gen

            # wrapper para control de errores en streaming
            def safe_response_gen():
                try:
                    for token in original_gen:
                        yield token
                except Exception as e:
                    logger.error("Error durante el streaming: %s", e)
                    if "429" in str(e) or "quota" in str(e).lower() or "limit" in str(e).lower():
                        yield "Error: El sistema está experimentando un alto volumen de consultas. Por favor, intenta de nuevo en unos segundos."
                    else:
                        yield f"Error: Ocurrió un error inesperado al procesar la consulta. ({str(e)})"

            response.response_gen = safe_response_gen()
            return response

        except Exception as e:
            logger.error("Error al iniciar consulta: %s", e)
            error_msg = "Error: El sistema está experimentando un alto volumen de consultas. Por favor, intenta de nuevo en unos segundos."
            if "404" in str(e):
                error_msg = "Error: Modelo no encontrado (HTTP 404). Por favor contacte al soporte técnico."
            elif not ("429" in str(e) or "quota" in str(e).lower() or "limit" in str(e).lower()):
                error_msg = f"Error al procesar la consulta: {str(e)}"

            def error_gen():
                yield error_msg

            return StreamingResponse(
                response_gen=error_gen(),
                source_nodes=[]
            )
