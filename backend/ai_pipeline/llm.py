"""
Language Model (LLM) Module — Abstract Adapters, Local Ollama & Groq Cloud Failover.

This module provides conversational reasoning for phone dialogue turns.
It orchestrates context-aware prompt construction, conversational history pruning,
and latency-bounded LLM generation:
- Primary: Qwen-14B (Ollama Q4_K_M) running locally on server GPU.
- Fallback: Groq Cloud API (LLaMA-3.3-70B) offering sub-second response times.

Invariants:
    - Conversational responses must remain under 35 words (<= 2 sentences) for voice UX.
    - History must be truncated to the last 6 messages (3 turns) to maintain low TTFT.
    - No markdown formatting, bullet points, asterisks, or lists in generated speech text.

Dependencies:
    - httpx >= 0.27
    - pydantic >= 2.0
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import httpx

from backend.config import settings

logger = logging.getLogger(__name__)

# Mandatory Telephony Guardrail appended to all LLM system prompts
TELEPHONY_VOICE_CONSTRAINT = (
    "\n\nCRITICAL VOICE CALL RULES: "
    "1. Speak naturally as if talking on a real telephone call. "
    "2. Keep your answer strictly under 2 short sentences (maximum 30 words). "
    "3. NEVER use markdown symbols, bold text, bullet points, asterisks, or numbered lists. "
    "4. Reply in the exact same language as the caller (Hindi, Gujarati, or English)."
)


class LLMAdapter(ABC):
    """
    Abstract interface for conversational Language Model engines.

    All implementations must be non-blocking and asynchronously compliant.
    """

    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        history: List[Dict[str, str]],
        user_input: str,
    ) -> str:
        """
        Generates the next conversational voice turn response.

        Args:
            system_prompt: Campaign-specific prompt defining role and business logic.
            history: List of prior turns formatted as [{'role': 'user'|'assistant', 'content': '...'}].
            user_input: Latest transcribed speech from the caller.

        Returns:
            str: Concise textual response ready for speech synthesis.

        Raises:
            LLMException: If inference fails across retries.
        """
        pass


class OllamaLLM(LLMAdapter):
    """
    Primary local LLM adapter communicating with the Ollama daemon over HTTP.

    Executes quantized Qwen-14B models on the server's local NVIDIA GPU,
    ensuring private student records never leave the university infrastructure.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: float = 4.0,
    ) -> None:
        """
        Initializes the Ollama LLM adapter.

        Args:
            base_url: HTTP endpoint of Ollama service (default from settings).
            model: Tagged model identifier (default: 'qwen3:14b').
            timeout_seconds: HTTP network timeout threshold.
        """
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.ollama_model
        self.timeout_seconds = timeout_seconds
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Returns or lazily creates a persistent pooled AsyncClient for local Ollama."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout_seconds, connect=1.5),
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=50),
            )
        return self._client

    async def aclose(self) -> None:
        """Gracefully closes persistent HTTP connection pool."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def generate(
        self,
        system_prompt: str,
        history: List[Dict[str, str]],
        user_input: str,
    ) -> str:
        """
        Submits a multi-turn chat completion request to the local Ollama API.

        Args:
            system_prompt: Base campaign instructions.
            history: Prior conversational message list.
            user_input: Current user utterance transcript.

        Returns:
            str: Synthesizable text answer.

        Raises:
            httpx.HTTPError: If the Ollama server returns an error code or times out.
        """
        full_system_prompt = f"{system_prompt}{TELEPHONY_VOICE_CONSTRAINT}"
        messages: List[Dict[str, str]] = [{"role": "system", "content": full_system_prompt}]

        # Telephony optimization: Keep only last 6 messages (3 conversational exchanges)
        pruned_history = history[-6:] if history else []
        messages.extend(pruned_history)
        messages.append({"role": "user", "content": user_input})

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 75,  # Strictly limit token count to prevent long generation
            },
        }

        endpoint = f"{self.base_url}/api/chat"
        client = await self._get_client()
        resp = await client.post(endpoint, json=payload)
        resp.raise_for_status()
        data = resp.json()
        message_obj = data.get("message", {})
        raw_content = message_obj.get("content", "").strip()

        # Clean any inadvertent markdown asterisks
        return raw_content.replace("*", "").replace("#", "").strip()


class GroqLLM(LLMAdapter):
    """
    Cloud fallback LLM adapter communicating with the Groq Cloud API.

    Leverages Groq's LPU architecture to achieve sub-second Time-to-First-Token (TTFT)
    on high-capability open-weight models (LLaMA-3.3-70B).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "qwen/qwen3.8-27b",
        timeout_seconds: float = 5.0,
    ) -> None:
        """
        Initializes the Groq LLM adapter.

        Args:
            api_key: Groq Cloud API secret key.
            model: Target model identifier on Groq infrastructure.
            timeout_seconds: Network request timeout.
        """
        self.api_key = api_key or settings.groq_api_key
        self.model = model
        self.endpoint = "https://api.groq.com/openai/v1/chat/completions"
        self.timeout_seconds = timeout_seconds
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Returns or lazily creates a persistent pooled AsyncClient for Groq Cloud."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout_seconds, connect=2.0),
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=50),
            )
        return self._client

    async def aclose(self) -> None:
        """Gracefully closes persistent HTTP connection pool."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def generate(
        self,
        system_prompt: str,
        history: List[Dict[str, str]],
        user_input: str,
    ) -> str:
        """
        Dispatches chat completion request to Groq Cloud API.

        Args:
            system_prompt: Base campaign instructions.
            history: Conversation turn history.
            user_input: Current user utterance.

        Returns:
            str: Generated conversational response.

        Raises:
            ValueError: If GROQ_API_KEY is missing.
            httpx.HTTPError: If the remote API fails.
        """
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not configured in environment variables.")

        full_system_prompt = f"{system_prompt}{TELEPHONY_VOICE_CONSTRAINT}"
        messages: List[Dict[str, str]] = [{"role": "system", "content": full_system_prompt}]
        messages.extend(history[-6:] if history else [])
        messages.append({"role": "user", "content": user_input})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 100,
            "temperature": 0.3,
        }

        client = await self._get_client()
        resp = await client.post(self.endpoint, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        return content.replace("*", "").replace("#", "").strip()


class FallbackLLM(LLMAdapter):
    """
    Composite LLM adapter providing automatic failover between local Ollama and Groq API.

    Guarantees that conversational turns are never dropped even if the local GPU
    is temporarily saturated or Ollama is restarting.
    """

    def __init__(
        self,
        primary: Optional[LLMAdapter] = None,
        fallback: Optional[LLMAdapter] = None,
        timeout_seconds: float = 3.5,
    ) -> None:
        """
        Initializes the FallbackLLM composite.

        Args:
            primary: Primary local LLM adapter (default: OllamaLLM).
            fallback: Cloud failover LLM adapter (default: GroqLLM).
            timeout_seconds: Execution deadline before triggering cloud fallback (default: 3.5s).
        """
        self.primary = primary or OllamaLLM()
        self.fallback = fallback or GroqLLM()
        self.timeout_seconds = timeout_seconds

    async def generate(
        self,
        system_prompt: str,
        history: List[Dict[str, str]],
        user_input: str,
    ) -> str:
        """
        Executes bounded LLM generation with automatic fallback to cloud.

        Args:
            system_prompt: System script instructions.
            history: Message history.
            user_input: User speech input.

        Returns:
            str: Synthesizable response text.
        """
        t0 = time.monotonic()
        try:
            logger.info("Generating response via primary Ollama LLM (timeout=%.1fs)...", self.timeout_seconds)
            reply = await asyncio.wait_for(
                self.primary.generate(system_prompt, history, user_input),
                timeout=self.timeout_seconds,
            )
            elapsed_ms = int((time.monotonic() - t0) * 1000)
            logger.info("Primary LLM completed in %d ms: '%s'", elapsed_ms, reply)
            return reply
        except (asyncio.TimeoutError, Exception) as exc:
            elapsed_ms = int((time.monotonic() - t0) * 1000)
            logger.warning(
                "Primary LLM failed or exceeded timeout (%d ms) with error '%s'. Triggering Groq API fallback...",
                elapsed_ms,
                exc,
            )
            t_fallback = time.monotonic()
            reply = await self.fallback.generate(system_prompt, history, user_input)
            fallback_ms = int((time.monotonic() - t_fallback) * 1000)
            logger.info("Fallback LLM completed in %d ms: '%s'", fallback_ms, reply)
            return reply
