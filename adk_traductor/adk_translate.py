from __future__ import annotations

import asyncio
import os
import uuid
from dataclasses import dataclass
from typing import Literal

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Conditional import for LiteLLM
try:
    from google.adk.models.lite_llm import LiteLlm
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False


@dataclass(frozen=True)
class AdkTranslateConfig:
    model: str = "gemini-2.5-flash"
    provider: Literal["gemini", "openai", "anthropic", "github"] | None = None
    app_name: str = "adk_md_translator"
    user_id: str = "translator"


class AdkTranslator:
    def __init__(self, config: AdkTranslateConfig | None = None):
        self._config = config or AdkTranslateConfig()

        # Determine model configuration
        model_config = self._prepare_model_config()

        self._agent = Agent(
            name="md_translator",
            model=model_config,
            description="Traduce Markdown del inglés al español preservando código.",
            instruction=(
                "Eres un traductor profesional de documentación técnica EN→ES.\n\n"
                "REGLAS ESTRICTAS:\n"
                "1. Traduce TODO el texto en español (títulos, párrafos, listas)\n"
                "2. Traduce COMENTARIOS dentro del código (#, //, /* */)\n"
                "3. PRESERVA EXACTAMENTE sin cambios:\n"
                "   - Bloques de código (```python, ```javascript, etc.) EXCEPTO comentarios\n"
                "   - Código inline entre backticks `como esto`\n"
                "   - URLs y links [texto](url)\n"
                "   - HTML tags y atributos\n"
                "   - Frontmatter YAML (---)\n"
                "   - Nombres de variables, funciones, clases, imports\n"
                "   - Paths, comandos, strings de código\n"
                "4. Mantén el formato Markdown idéntico\n"
                "5. NO agregues explicaciones, solo devuelve el Markdown traducido\n\n"
                "Devuelve SOLO el documento traducido, sin prefacios ni metadata."
            ),
            tools=[],
        )

    def _prepare_model_config(self) -> str | object:
        """Prepara la configuración del modelo según el provider."""
        provider = self._config.provider
        model = self._config.model

        # Sin provider o gemini explícito -> string directo (default behavior)
        if provider is None or provider == "gemini":
            return model

        # Provider externo -> requiere LiteLLM
        if not LITELLM_AVAILABLE:
            raise RuntimeError(
                f"Provider '{provider}' requiere LiteLLM. Instala: pip install litellm"
            )

        # Mapeo provider -> LiteLLM format
        provider_prefixes = {
            "openai": "openai/",
            "anthropic": "anthropic/",
            "github": "github/",  # GitHub models via LiteLLM
        }

        prefix = provider_prefixes.get(provider)
        if prefix is None:
            raise ValueError(f"Provider no soportado: {provider}")

        litellm_model = f"{prefix}{model}"
        return LiteLlm(model=litellm_model)

    def _ensure_api_key(self) -> None:
        if not os.getenv("GOOGLE_API_KEY"):
            raise RuntimeError(
                "Falta GOOGLE_API_KEY en el entorno. Configúrala para usar Gemini."
            )

    async def translate_text(self, text: str) -> str:
        self._ensure_api_key()

        session_service = InMemorySessionService()
        runner = Runner(
            agent=self._agent,
            app_name=self._config.app_name,
            session_service=session_service,
        )

        session_id = str(uuid.uuid4())
        await session_service.create_session(
            app_name=self._config.app_name,
            user_id=self._config.user_id,
            session_id=session_id,
        )

        content = types.Content(role="user", parts=[types.Part(text=text)])

        final_text = None
        async for event in runner.run_async(
            user_id=self._config.user_id, session_id=session_id, new_message=content
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    final_text = event.content.parts[0].text
                break

        if final_text is None:
            raise RuntimeError("El agente no devolvió respuesta final.")

        return final_text
