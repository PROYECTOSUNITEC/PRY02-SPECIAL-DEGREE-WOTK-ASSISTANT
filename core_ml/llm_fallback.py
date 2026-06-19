import os
import time
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    # respuesta unificada
    text: str
    provider: str
    model: str


class BaseLLMProvider(ABC):
    # interfaz base
    name: str = ""
    model: str = ""

    @abstractmethod
    def generate(self, system_prompt: str, context: str, user_query: str) -> LLMResponse:
        # genera respuesta
        ...


class GroqProvider(BaseLLMProvider):
    # groq
    name = "groq"
    model = "llama-3.3-70b-versatile"

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY no configurada")
        from groq import Groq
        self._client = Groq(api_key=api_key)

    def generate(self, system_prompt: str, context: str, user_query: str) -> LLMResponse:
        # separar system y user
        messages = [
            {
                "role": "system",
                "content": f"{system_prompt}\n\nCONTEXTO RECUPERADO:\n{context}",
            },
            {
                "role": "user",
                "content": user_query,
            },
        ]

        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.1,
            max_tokens=4096,
        )

        return LLMResponse(
            text=response.choices[0].message.content,
            provider=self.name,
            model=self.model,
        )


class CohereProvider(BaseLLMProvider):
    # cohere
    name = "cohere"
    model = "command-r-08-2024"

    def __init__(self):
        api_key = os.getenv("COHERE_API_KEY")
        if not api_key:
            raise ValueError("COHERE_API_KEY no configurada")
        import cohere
        self._client = cohere.Client(api_key=api_key)

    def generate(self, system_prompt: str, context: str, user_query: str) -> LLMResponse:
        # preamble aislado
        preamble = f"{system_prompt}\n\nCONTEXTO RECUPERADO:\n{context}"

        response = self._client.chat(
            model=self.model,
            preamble=preamble,
            message=user_query,
            temperature=0.1,
        )

        return LLMResponse(
            text=response.text,
            provider=self.name,
            model=self.model,
        )


class GeminiProvider(BaseLLMProvider):
    # gemini
    name = "gemini"
    model = "gemini-flash-latest"

    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY no configurada")
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self._genai = genai

    def generate(self, system_prompt: str, context: str, user_query: str) -> LLMResponse:
        # system_instruction separado
        model = self._genai.GenerativeModel(
            model_name=f"models/{self.model}",
            system_instruction=system_prompt,
            generation_config={"temperature": 0.1, "max_output_tokens": 4096},
        )

        prompt = f"CONTEXTO RECUPERADO:\n{context}\n\nPREGUNTA DEL USUARIO:\n{user_query}"
        response = model.generate_content(prompt)

        return LLMResponse(
            text=response.text,
            provider=self.name,
            model=self.model,
        )


# prioridad
PROVIDER_PRIORITY = [GroqProvider, CohereProvider, GeminiProvider]


class LLMFallbackCarousel:
    # carrusel con fallback

    def __init__(self, provider_classes: list[type[BaseLLMProvider]] | None = None):
        self._providers: list[BaseLLMProvider] = []
        classes = provider_classes or PROVIDER_PRIORITY
        self._init_providers(classes)

    def _init_providers(self, classes: list[type[BaseLLMProvider]]):
        for cls in classes:
            try:
                provider = cls()
                self._providers.append(provider)
                logger.info("proveedor %s inicializado [modelo: %s]", provider.name, provider.model)
            except Exception as e:
                logger.warning("proveedor %s no disponible: %s", cls.__name__, e)

        if not self._providers:
            raise RuntimeError("ningun proveedor llm disponible")

    def generate(self, system_prompt: str, context: str, user_query: str, provider_name: str | None = None) -> LLMResponse:
        # ejecutar con un proveedor específico o con fallback
        if provider_name and provider_name != "auto":
            target = next((p for p in self._providers if p.name == provider_name), None)
            if not target:
                raise ValueError(f"proveedor {provider_name} no disponible")
            logger.info("intentando con proveedor forzado: %s", target.name)
            return target.generate(system_prompt, context, user_query)

        # ejecutar con fallback
        errors: list[tuple[str, str]] = []

        for provider in self._providers:
            try:
                logger.info("intentando con proveedor: %s", provider.name)
                start = time.time()
                response = provider.generate(system_prompt, context, user_query)
                elapsed = time.time() - start
                logger.info(
                    "respuesta de %s en %.2fs [modelo: %s]",
                    provider.name, elapsed, provider.model,
                )
                return response

            except Exception as e:
                elapsed = time.time() - start
                logger.warning(
                    "fallo en %s (%.2fs): %s — conmutando...",
                    provider.name, elapsed, str(e)[:200],
                )
                errors.append((provider.name, str(e)))
                continue

        # error si todos fallan
        error_summary = "; ".join(f"[{name}] {err[:100]}" for name, err in errors)
        raise RuntimeError(f"todas las apis fallaron: {error_summary}")


    @property
    def available_providers(self) -> list[str]:
        return [p.name for p in self._providers]
