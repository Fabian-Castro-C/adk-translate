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
            f"Eres un traductor profesional de documentación técnica EN→ES.\n\n"
            f"REGLAS ESTRICTAS:\n"
            f"1. Traduce TODO el texto en español (títulos, párrafos, listas)\n"
            f"2. Traduce COMENTARIOS dentro del código (#, //, /* */)\n"
            f"3. PRESERVA EXACTAMENTE sin cambios:\n"
            f"   - Bloques de código (```python, ```javascript, etc.) EXCEPTO comentarios\n"
            f"   - Código inline entre backticks `como esto`\n"
            f"   - URLs y links [texto](url)\n"
            f"   - HTML tags y atributos\n"
            f"   - Frontmatter YAML (---)\n"
            f"   - Nombres de variables, funciones, clases, imports\n"
            f"   - Paths, comandos, strings de código\n"
            f"4. Mantén el formato Markdown idéntico\n"
            f"5. NO agregues explicaciones, solo devuelve el Markdown traducido\n\n"
            f"Devuelve SOLO el documento traducido, sin prefacios ni metadata.\n\n"
            f"---\n\n"
            f"{text}"
        )
        
        response = await self._session.send_and_wait({"prompt": prompt})
        
        if response and response.data and hasattr(response.data, 'content'):
            return response.data.content.strip()
        
        raise RuntimeError("Copilot SDK no devolvió respuesta válida.")

    async def cleanup(self):
        """Cleanup Copilot client resources."""
        if self._client is not None:
            await self._client.stop()
            self._client = None
            self._session = None
