"""Custom ADK model wrapper for the GitHub Copilot SDK.

Note: the PyPI package is named `github-copilot-sdk`, but it is imported as the
Python module `copilot`.
"""
from __future__ import annotations

import asyncio
import os
from typing import AsyncGenerator
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types

_copilot_import_error: Exception | None = None
try:
    # `github-copilot-sdk` installs/imports as `copilot`
    from copilot import CopilotClient
    COPILOT_SDK_AVAILABLE = True
except ImportError as e:
    COPILOT_SDK_AVAILABLE = False
    _copilot_import_error = e


class CopilotModel(BaseLlm):
    """ADK-compatible model wrapper for GitHub Copilot SDK."""
    
    def __init__(self, model: str = "gpt-4.1"):
        if not COPILOT_SDK_AVAILABLE:
            raise ImportError(
                "GitHub Copilot SDK no está instalado (PyPI: 'github-copilot-sdk', import: 'copilot'). "
                "Instala: uv sync --extra copilot"
            ) from _copilot_import_error
        super().__init__(model=model)
        self._client = None
        self._session = None
    
    async def _ensure_session(self):
        """Initialize Copilot client if not already done."""
        if self._client is None:
            self._client = CopilotClient()
            await self._client.start()
    
    async def generate_content_async(
        self,
        llm_request: LlmRequest,
        stream: bool = False,
    ) -> AsyncGenerator[LlmResponse, None]:
        """Generate response from Copilot."""
        await self._ensure_session()
        
        # Create NEW session for each request to avoid welcome message interference
        session = await self._client.create_session()
        
        # Wait a moment for welcome message to pass
        await asyncio.sleep(0.5)
        
        # Convert LlmRequest to simple text prompt
        prompt_text = self._convert_request_to_text(llm_request)
        
        # Setup event tracking
        message_received = asyncio.Event()
        response_chunks: list[str] = []
        got_user_message = False
        capturing_turn = False
        debug = os.getenv("ADK_TRADUCTOR_DEBUG_COPILOT") == "1"

        def _is_welcome_message(text: str) -> bool:
            t = text.lower()
            return "github copilot cli" in t and "what would you like" in t
        
        def handler(event):
            nonlocal got_user_message, capturing_turn
            event_type = event.type.value

            if debug:
                try:
                    preview = ""
                    if hasattr(event.data, "content") and event.data.content:
                        preview = event.data.content.replace("\n", " ")[:120]
                    print(f"[copilot] event={event_type} preview={preview!r}")
                except Exception:
                    pass
            
            # Track when OUR user message is confirmed
            if event_type == "user.message":
                got_user_message = True
            elif event_type == "assistant.turn_start" and got_user_message:
                capturing_turn = True
                response_chunks.clear()
            elif event_type == "assistant.message" and got_user_message and capturing_turn and not message_received.is_set():
                if hasattr(event.data, "content") and event.data.content:
                    # Sometimes Copilot CLI emits a fixed greeting; ignore it and keep waiting.
                    if not response_chunks and _is_welcome_message(event.data.content):
                        return
                    response_chunks.append(event.data.content)
                    # Unblock as soon as we have any assistant content. Some environments
                    # may not emit turn_end reliably for long responses.
                    message_received.set()
            elif event_type == "assistant.turn_end" and got_user_message and capturing_turn and not message_received.is_set():
                message_received.set()
        
        # Subscribe to events
        unsubscribe = session.on(handler)
        
        try:
            # Send prompt
            await session.send({"prompt": prompt_text})
            
            # Wait for assistant response (120s timeout for long translations)
            timeout_s = float(os.getenv("ADK_TRADUCTOR_COPILOT_TIMEOUT", "300"))
            await asyncio.wait_for(message_received.wait(), timeout=timeout_s)

            # Small grace window to capture additional message chunks, if any.
            await asyncio.sleep(0.25)
            
            # Yield response
            response_content = "".join(response_chunks).strip()
            yield LlmResponse(
                content=types.Content(parts=[types.Part(text=response_content or "")]),
                partial=False,
                turn_complete=True,
            )
        finally:
            unsubscribe()
            # Clean up session
            try:
                await self._client.delete_session(session.session_id)
            except Exception:
                pass
    
    def _convert_request_to_text(self, llm_request: LlmRequest) -> str:
        """Convert LlmRequest to simple text prompt."""
        debug = os.getenv("ADK_TRADUCTOR_DEBUG_COPILOT") == "1"
        chunks: list[str] = []

        def _append_text_from_content(content: object) -> None:
            parts = getattr(content, "parts", None) or []
            for part in parts:
                if hasattr(part, "text") and part.text:
                    chunks.append(part.text)

        # 1) System instruction (often where Agent.instruction lands)
        saw_system = False
        cfg = getattr(llm_request, "config", None)
        sys_inst = getattr(cfg, "system_instruction", None) if cfg is not None else None
        if sys_inst is not None:
            if isinstance(sys_inst, str):
                if sys_inst.strip():
                    chunks.append(sys_inst.strip())
                    saw_system = True
            else:
                # Usually a types.Content
                if hasattr(sys_inst, "parts") and getattr(sys_inst, "parts"):
                    _append_text_from_content(sys_inst)
                    saw_system = True

        # 2) Conversation contents (include both system + user)
        contents = getattr(llm_request, "contents", None) or []
        if debug:
            try:
                print(f"[copilot] llm_request.model={getattr(llm_request, 'model', None)} contents={len(contents)}")
                for i, c in enumerate(contents[:8]):
                    role = getattr(c, "role", None)
                    preview = ""
                    parts = getattr(c, "parts", None) or []
                    for p in parts:
                        if hasattr(p, "text") and p.text:
                            preview = p.text.replace("\n", " ")[:90]
                            break
                    print(f"[copilot] content[{i}] role={role} preview={preview!r}")
            except Exception:
                pass

        for c in contents:
            role = getattr(c, "role", None)
            if role == "system":
                saw_system = True
                chunks.append("SYSTEM:")
                _append_text_from_content(c)
                continue
            if role == "user" or role is None:
                chunks.append("USER:")
                _append_text_from_content(c)
                continue
            # Ignore assistant/model/tool messages

        prompt = "\n\n".join(x for x in chunks if x and x.strip()).strip()

        # 3) Fail-fast: require a system instruction.
        # We rely on a system message to prevent generic assistant behavior.
        if not saw_system:
            raise RuntimeError(
                "CopilotModel requiere una instrucción de sistema (system) pero ADK no la incluyó en el request. "
                "Asegúrate de inyectar un mensaje role='system' (por ejemplo, con las reglas del traductor) antes del mensaje del usuario."
            )

        return prompt
