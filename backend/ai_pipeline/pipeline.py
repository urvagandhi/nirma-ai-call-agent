"""
AI Pipeline Orchestrator Module — STT -> LLM -> TTS Cascaded Engine.

This module coordinates the complete multi-stage conversational turn pipeline:
1. Speech-to-Text (STT): Transcribes input caller audio to text.
2. Large Language Model (LLM): Generates context-aware, voice-optimized response.
3. Text-to-Speech (TTS): Synthesizes response text into audio and returns public static URL.

Performance & Latency Requirements:
    - Target total turnaround latency: < 4,000 ms.
    - STT budget: < 1,200 ms | LLM budget: < 1,800 ms | TTS budget: < 600 ms.
    - Instruments per-stage timing metrics and appends latency logs to session context.

Dependencies:
    - backend.ai_pipeline.stt
    - backend.ai_pipeline.llm
    - backend.ai_pipeline.tts
"""

import logging
import time
from typing import Any, Dict, Optional, Tuple

from backend.ai_pipeline.llm import FallbackLLM, LLMAdapter
from backend.ai_pipeline.stt import FallbackSTT, STTAdapter
from backend.ai_pipeline.tts import FallbackTTS, TTSAdapter

logger = logging.getLogger(__name__)


class AIPipeline:
    """
    Cascaded AI voice pipeline orchestrating STT, LLM, and TTS adapters.

    Attributes:
        stt: Configured STT adapter instance (with local/cloud fallback).
        llm: Configured LLM adapter instance (with local/cloud fallback).
        tts: Configured TTS adapter instance (with local/cloud fallback).
    """

    def __init__(
        self,
        stt: Optional[STTAdapter] = None,
        llm: Optional[LLMAdapter] = None,
        tts: Optional[TTSAdapter] = None,
    ) -> None:
        """
        Initializes the AI pipeline with default fallback-enabled adapters.

        Args:
            stt: Custom STT adapter or None for default FallbackSTT.
            llm: Custom LLM adapter or None for default FallbackLLM.
            tts: Custom TTS adapter or None for default FallbackTTS.
        """
        self.stt = stt or FallbackSTT()
        self.llm = llm or FallbackLLM()
        self.tts = tts or FallbackTTS()
        logger.info("AIPipeline initialized with fallback-enabled stages (STT, LLM, TTS).")

    async def process_turn(
        self,
        audio_url: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Executes a single conversational voice turn end-to-end.

        Args:
            audio_url: Publicly reachable URL of caller's recorded speech.
            call_context: Session context dictionary containing:
                - 'system_prompt': Active script prompt.
                - 'history': List of previous turn dictionaries.
                - 'lang': Language code ('hi', 'gu', 'en').
                - 'turn': Current turn integer counter.
                - 'latency_log': List where latency telemetry is appended.

        Returns:
            Dict[str, Any]: Dictionary containing:
                - 'user_transcript': Transcribed user speech text.
                - 'assistant_reply': Synthesizable assistant answer text.
                - 'response_audio_url': Public static URL of synthesized response WAV.
                - 'latency': Dict with stage latencies in milliseconds.
                - 'exceeded_budget': Boolean flag indicating whether turnaround > 4000ms.

        Raises:
            Exception: If any pipeline stage unrecoverably fails.
        """
        turn_id = context.get("turn", 1)
        lang = context.get("lang", "hi")
        system_prompt = context.get("system_prompt", "")
        history = context.get("history", [])

        logger.info("Processing conversational turn %d (Language: %s)", turn_id, lang)
        t_start = time.monotonic()

        # ----------------------------------------------------------------------
        # Stage 1: Speech-to-Text (STT)
        # ----------------------------------------------------------------------
        t0 = time.monotonic()
        user_transcript = await self.stt.transcribe(audio_url=audio_url, language=lang)
        stt_ms = int((time.monotonic() - t0) * 1000)
        logger.info("Turn %d [Stage 1 STT] completed in %d ms", turn_id, stt_ms)

        # ----------------------------------------------------------------------
        # Stage 2: Response Generation (LLM)
        # ----------------------------------------------------------------------
        t0 = time.monotonic()
        assistant_reply = await self.llm.generate(
            system_prompt=system_prompt,
            history=history,
            user_input=user_transcript,
        )
        llm_ms = int((time.monotonic() - t0) * 1000)
        logger.info("Turn %d [Stage 2 LLM] completed in %d ms", turn_id, llm_ms)

        # ----------------------------------------------------------------------
        # Stage 3: Speech Synthesis (TTS)
        # ----------------------------------------------------------------------
        t0 = time.monotonic()
        response_audio_url = await self.tts.synthesize(
            text=assistant_reply,
            language=lang,
        )
        tts_ms = int((time.monotonic() - t0) * 1000)
        logger.info("Turn %d [Stage 3 TTS] completed in %d ms", turn_id, tts_ms)

        total_ms = int((time.monotonic() - t_start) * 1000)
        exceeded_budget = total_ms > 4000

        latency_info = {
            "turn": turn_id,
            "stt_ms": stt_ms,
            "llm_ms": llm_ms,
            "tts_ms": tts_ms,
            "total_ms": total_ms,
            "exceeded_budget": exceeded_budget,
        }

        # Record telemetry in session context
        if "latency_log" not in context:
            context["latency_log"] = []
        context["latency_log"].append(latency_info)

        if exceeded_budget:
            logger.warning(
                "Turn %d EXCEEDED 4000ms latency budget! Total: %d ms (STT: %d, LLM: %d, TTS: %d)",
                turn_id,
                total_ms,
                stt_ms,
                llm_ms,
                tts_ms,
            )
        else:
            logger.info("Turn %d completed within budget in %d ms total", turn_id, total_ms)

        return {
            "user_transcript": user_transcript,
            "assistant_reply": assistant_reply,
            "response_audio_url": response_audio_url,
            "latency": latency_info,
            "exceeded_budget": exceeded_budget,
        }
