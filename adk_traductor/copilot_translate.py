from __future__ import annotations

import asyncio
from dataclasses import dataclass

# Conditional import for Copilot SDK
try:
    from copilot import CopilotClient
    COPILOT_SDK_AVAILABLE = True
except ImportError:
    COPILOT_SDK_AVAILABLE = False


@dataclass(frozen=True)
class CopilotTranslateConfig:
    model: str = "gpt-4.1"


class CopilotTranslator:
    """Translator using GitHub Copilot SDK (uses local Copilot CLI)."""
    
    def __init__(self, config: CopilotTranslateConfig | None = None):
        if not COPILOT_SDK_AVAILABLE:
            raise RuntimeError(
                "Copilot SDK no disponible. Instala: pip install github-copilot-sdk\n"
                "Requisitos: GitHub Copilot CLI instalado y 'copilot' en PATH"
            )
        
        self._config = config or CopilotTranslateConfig()
        self._client = None
        self._session = None

    async def _ensure_session(self):
        """Lazy initialization of Copilot client and session."""
        if self._session is None:
            self._client = CopilotClient()
            await self._client.start()
            
            self._session = await self._client.create_session({
                "model": self._config.model,
            })

    async def translate_text(self, text: str) -> str:
        """Translate text using Copilot SDK."""
        await self._ensure_session()
        
        prompt = (
            f"Eres un traductor profesional EN→ES.\n"
            f"Reglas estrictas:\n"
            f"- Devuelve SOLO el texto traducido, sin prefacios ni comillas.\n"
            f"- Preserva EXACTAMENTE cualquier token placeholder con la forma <<ADK_Pn>>.\n"
            f"- No inventes contenido ni cambies formato innecesariamente.\n"
            f"- Mantén Markdown tal cual (saltos de línea, viñetas), solo traduce texto.\n\n"
            f"Texto a traducir:\n{text}"
        )
        
        response = await self._session.send_and_wait({"prompt": prompt})
        
        if response and response.data and hasattr(response.data, 'content'):
            return response.data.content.strip()
        
        raise RuntimeError("Copilot SDK no devolvió respuesta válida.")

    async def translate_many_texts(
        self, texts: list[str], *, jobs: int = 4
    ) -> list[str]:
        """Translate multiple texts concurrently."""
        sem = asyncio.Semaphore(jobs)

        async def _translate_with_limit(t: str) -> str:
            async with sem:
                return await self.translate_text(t)

        return await asyncio.gather(*[_translate_with_limit(t) for t in texts])

    async def cleanup(self):
        """Cleanup Copilot client resources."""
        if self._client is not None:
            await self._client.stop()
            self._client = None
            self._session = None
