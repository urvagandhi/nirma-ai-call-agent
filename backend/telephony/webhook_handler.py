"""
Plivo Webhook Handler Module — Event-Driven Call State Machine & Plivo XML Gateway.

This module implements the HTTP endpoints triggered by Plivo carrier webhooks:
1. POST /webhook/plivo/answer: Triggered when recipient picks up the phone.
2. POST /webhook/plivo/input: Triggered when Plivo finishes recording student speech.
3. POST /webhook/plivo/hangup: Triggered when call disconnects.
4. POST /webhook/plivo/fallback: Triggered on carrier XML error.

CRITICAL TELEPHONY INVARIANTS:
    - Parameter name invariant: Plivo sends 'RecordUrl', NOT 'RecordingUrl' (Twilio).
    - Redis session keys 'call:session:{call_uuid}' MUST have an explicit TTL=600s.
    - Responses return application/xml constructed using standard XML tags.

Dependencies:
    - fastapi >= 0.111
    - redis >= 5.0
    - plivo >= 4.38
"""

import json
import logging
import time
import xml.etree.ElementTree as ET
from typing import Any, Dict, Optional

import redis.asyncio as aioredis
from fastapi import APIRouter, Form, HTTPException, Query, Response, status
from sqlalchemy import select

from backend.ai_pipeline.pipeline import AIPipeline
from backend.config import settings
from backend.database.models import CallLog, CallScript, CallTask
from backend.database.session import async_session_scope

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook/plivo", tags=["Plivo Webhooks"])

# Initialize lazy Redis client connection
redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)

# Shared AI Pipeline instance
ai_pipeline = AIPipeline()


def _build_plivo_xml_response(
    audio_url: Optional[str] = None,
    action_url: Optional[str] = None,
    hangup: bool = False,
    silence_seconds: int = 2,
) -> str:
    """
    Constructs valid Plivo XML response string.

    Args:
        audio_url: Optional static audio URL to play to the caller.
        action_url: Webhook action URL for the <Record> tag.
        hangup: If True, appends <Hangup/> directive after playing audio.
        silence_seconds: Silence detection threshold in seconds.

    Returns:
        str: Serialized XML document string.
    """
    response_elem = ET.Element("Response")

    if audio_url:
        play_elem = ET.SubElement(response_elem, "Play")
        play_elem.text = audio_url

    if hangup:
        ET.SubElement(response_elem, "Hangup")
    elif action_url:
        record_elem = ET.SubElement(
            response_elem,
            "Record",
            attrib={
                "action": action_url,
                "maxLength": "30",
                "silence": str(silence_seconds),
                "finishOnKey": "#",
                "redirect": "false",
            },
        )

    return ET.tostring(response_elem, encoding="utf-8", method="xml").decode("utf-8")


@router.post("/answer")
async def handle_answer(
    task_id: int = Query(..., description="Internal CallTask primary key"),
    call_uuid: str = Form(..., alias="CallUUID"),
    from_number: str = Form(..., alias="From"),
    to_number: str = Form(..., alias="To"),
) -> Response:
    """
    Triggered by Plivo when the student answers an outbound call.

    Loads the campaign script, initializes Redis session state with TTL=600s,
    and returns Plivo XML playing the opening greeting and recording student input.
    """
    logger.info(
        "Plivo Answer Webhook -> TaskID: %d, CallUUID: %s, From: %s, To: %s",
        task_id,
        call_uuid,
        from_number,
        to_number,
    )

    # 1. Fetch task and script details from database
    async with async_session_scope() as session:
        result = await session.execute(
            select(CallTask, CallScript)
            .join(CallScript, CallTask.script_id == CallScript.id)
            .where(CallTask.id == task_id)
        )
        row = result.first()
        if not row:
            logger.error("CallTask ID %d not found in database for answer webhook.", task_id)
            xml_resp = _build_plivo_xml_response(hangup=True)
            return Response(content=xml_resp, media_type="application/xml")

        task, script = row
        task.status = "in_progress"
        task.plivo_uuid = call_uuid
        task.answered_at = task.answered_at or task.created_at

    # 2. Synthesize initial opening message audio URL via TTS
    opening_text = script.opening_message
    language = script.language or "hi"
    opening_audio_url = await ai_pipeline.tts.synthesize(text=opening_text, language=language)

    # 3. Store in-flight session context in Redis (TTL=600 seconds)
    session_key = f"call:session:{call_uuid}"
    session_data = {
        "task_id": str(task_id),
        "call_uuid": call_uuid,
        "system_prompt": script.system_prompt,
        "opening_message": opening_text,
        "lang": language,
        "turn_count": "1",
        "history": json.dumps([{"role": "assistant", "content": opening_text}]),
        "start_time": str(time.time()),
    }

    await redis_client.hset(session_key, mapping=session_data)
    await redis_client.expire(session_key, 600)  # Mandatory 600s TTL
    logger.info("Initialized Redis call session key '%s' with TTL=600s", session_key)

    # 4. Construct Plivo XML response
    input_action_url = settings.build_webhook_url(f"/webhook/plivo/input?task_id={task_id}")
    xml_content = _build_plivo_xml_response(
        audio_url=opening_audio_url,
        action_url=input_action_url,
        silence_seconds=2,
    )

    return Response(content=xml_content, media_type="application/xml")


@router.post("/input")
async def handle_input(
    task_id: int = Query(..., description="Internal CallTask primary key"),
    call_uuid: str = Form(..., alias="CallUUID"),
    record_url: Optional[str] = Form(None, alias="RecordUrl"),
    recording_url: Optional[str] = Form(None, alias="RecordingUrl"),
) -> Response:
    """
    Triggered by Plivo when student finishes speaking.

    PLIVO PARAMETER INVARIANT: Reads 'RecordUrl' (with fallback to 'RecordingUrl').
    Executes AI pipeline turn, updates Redis session, and returns response XML.
    """
    actual_record_url = record_url or recording_url
    if not actual_record_url:
        logger.error("Missing RecordUrl parameter in Plivo input webhook for CallUUID %s", call_uuid)
        xml_resp = _build_plivo_xml_response(hangup=True)
        return Response(content=xml_resp, media_type="application/xml")

    logger.info(
        "Plivo Input Webhook -> TaskID: %d, CallUUID: %s, RecordURL: %s",
        task_id,
        call_uuid,
        actual_record_url,
    )

    # 1. Load Redis session context
    session_key = f"call:session:{call_uuid}"
    session_data = await redis_client.hgetall(session_key)

    if not session_data:
        logger.warning("Redis session key '%s' expired or missing. Terminating call.", session_key)
        xml_resp = _build_plivo_xml_response(hangup=True)
        return Response(content=xml_resp, media_type="application/xml")

    # Reconstitute context dictionary
    history_list = json.loads(session_data.get("history", "[]"))
    turn_count = int(session_data.get("turn_count", "1")) + 1
    lang = session_data.get("lang", "hi")
    system_prompt = session_data.get("system_prompt", "")

    context: Dict[str, Any] = {
        "task_id": task_id,
        "call_uuid": call_uuid,
        "system_prompt": system_prompt,
        "history": history_list,
        "lang": lang,
        "turn": turn_count,
        "latency_log": [],
    }

    # 2. Run cascaded AI pipeline turn (STT -> LLM -> TTS)
    try:
        turn_result = await ai_pipeline.process_turn(
            audio_url=actual_record_url,
            context=context,
        )
        user_transcript = turn_result["user_transcript"]
        assistant_reply = turn_result["assistant_reply"]
        response_audio_url = turn_result["response_audio_url"]
    except Exception as exc:
        logger.error("AI pipeline turn failure for task %d: %s", task_id, exc, exc_info=True)
        # Fallback audio prompt
        response_audio_url = await ai_pipeline.tts.synthesize(
            "Main aapki baat samajh nahi paya. Kripya punah prayas karen.", lang
        )
        assistant_reply = "Main aapki baat samajh nahi paya."
        user_transcript = ""

    # 3. Update history and turn count in Redis
    if user_transcript:
        history_list.append({"role": "user", "content": user_transcript})
    history_list.append({"role": "assistant", "content": assistant_reply})

    await redis_client.hset(
        session_key,
        mapping={
            "history": json.dumps(history_list),
            "turn_count": str(turn_count),
        },
    )
    await redis_client.expire(session_key, 600)  # Refresh 600s TTL

    # 4. Check call termination criteria (max 10 turns or explicit goodbye)
    should_hangup = turn_count >= 10 or any(
        kw in assistant_reply.lower() for kw in ["goodbye", "dhanyavaad", "alvida", "thank you"]
    )

    input_action_url = settings.build_webhook_url(f"/webhook/plivo/input?task_id={task_id}")
    xml_content = _build_plivo_xml_response(
        audio_url=response_audio_url,
        action_url=input_action_url if not should_hangup else None,
        hangup=should_hangup,
        silence_seconds=2,
    )

    return Response(content=xml_content, media_type="application/xml")


@router.post("/hangup")
async def handle_hangup(
    task_id: int = Query(..., description="Internal CallTask primary key"),
    call_uuid: str = Form(..., alias="CallUUID"),
    duration: int = Form(0, alias="Duration"),
) -> Response:
    """
    Triggered by Plivo when the call is disconnected.

    Updates PostgreSQL CallTask status, serializes conversation transcript
    into CallLog, and cleans up Redis session keys.
    """
    logger.info(
        "Plivo Hangup Webhook -> TaskID: %d, CallUUID: %s, Duration: %ds",
        task_id,
        call_uuid,
        duration,
    )

    session_key = f"call:session:{call_uuid}"
    session_data = await redis_client.hgetall(session_key)
    history_list = json.loads(session_data.get("history", "[]")) if session_data else []

    # Update database records
    async with async_session_scope() as session:
        task_res = await session.execute(select(CallTask).where(CallTask.id == task_id))
        task = task_res.scalar_one_or_none()

        if task:
            task.status = "completed"
            task.duration_sec = duration
            task.outcome = "completed" if duration > 5 else "no_answer"
            task.ended_at = task.ended_at or task.created_at

            # Save full transcript log
            log_res = await session.execute(select(CallLog).where(CallLog.task_id == task_id))
            call_log = log_res.scalar_one_or_none()
            if not call_log:
                call_log = CallLog(
                    task_id=task_id,
                    transcript=history_list,
                    stt_provider="indic_conformer",
                    llm_provider="qwen3",
                    tts_provider="indicf5",
                    avg_latency_ms=1800,
                )
                session.add(call_log)
            else:
                call_log.transcript = history_list

    # Delete Redis session context
    await redis_client.delete(session_key)

    xml_content = _build_plivo_xml_response(hangup=True)
    return Response(content=xml_content, media_type="application/xml")


@router.post("/fallback")
async def handle_fallback() -> Response:
    """Triggered by Plivo on XML execution error; ensures graceful call hangup."""
    logger.error("Plivo Webhook Fallback triggered due to XML parsing or carrier routing failure.")
    xml_content = _build_plivo_xml_response(hangup=True)
    return Response(content=xml_content, media_type="application/xml")
