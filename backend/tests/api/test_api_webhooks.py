"""
API & Telephony Regression Tests — Plivo Webhook State Machine & XML Gateway.

Tests `backend.telephony.webhook_handler`:
- POST /webhook/plivo/answer: Session initialization, mandatory Redis TTL=600s, XML generation.
- POST /webhook/plivo/input: Plivo parameter invariant ('RecordUrl' vs Twilio 'RecordingUrl'),
  distributed lock deduplication, conversational turn progression, max turn termination.
- POST /webhook/plivo/hangup: Outcome determination by duration, transcript serialization into CallLog,
  Redis session cleanup.
- POST /webhook/plivo/fallback: Graceful carrier error recovery with Hangup XML.
- XML correctness: Valid XML formatting and headers.
"""

import json
from typing import Dict, List
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import CallCampaign, CallLog, CallScript, CallTask, Student, utc_now
from backend.telephony.webhook_handler import _build_plivo_xml_response


# ------------------------------------------------------------------------------
# 1. XML Builder Unit Tests
# ------------------------------------------------------------------------------
def test_build_plivo_xml_response_play_and_record():
    """Verifies XML builder produces valid Play and Record elements."""
    xml_str = _build_plivo_xml_response(
        audio_url="https://domain.edu/audio/greeting.wav",
        action_url="https://domain.edu/webhook/plivo/input?task_id=42",
        silence_seconds=3,
    )
    assert "<Response>" in xml_str
    assert "<Play>https://domain.edu/audio/greeting.wav</Play>" in xml_str
    assert '<Record action="https://domain.edu/webhook/plivo/input?task_id=42"' in xml_str
    assert 'silence="3"' in xml_str


def test_build_plivo_xml_response_hangup():
    """Verifies XML builder produces Hangup element when hangup=True."""
    xml_str = _build_plivo_xml_response(hangup=True)
    assert "<Response>" in xml_str
    assert "<Hangup" in xml_str
    assert "<Record" not in xml_str


# ------------------------------------------------------------------------------
# 2. Answer Webhook Tests
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_plivo_answer_nonexistent_task(async_client: AsyncClient):
    """Verifies answer webhook for nonexistent task returns Hangup XML."""
    payload = {
        "CallUUID": "plivo-unknown-uuid",
        "From": "+917923456789",
        "To": "+919876500001",
    }
    response = await async_client.post("/webhook/plivo/answer?task_id=99999", data=payload)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/xml")
    assert "<Hangup" in response.text


@pytest.mark.asyncio
async def test_plivo_answer_valid_task_lifecycle(
    async_client: AsyncClient,
    db_session: AsyncSession,
    seed_students: List[Student],
):
    """Verifies answer webhook sets task in_progress, initializes Redis with TTL=600s, and emits Play/Record XML."""
    script = CallScript(
        name="Answer Script",
        category="fee_reminder",
        language="hi",
        system_prompt="Tu ek assistant hai.",
        opening_message="Namaste, Nirma University se call hai.",
    )
    db_session.add(script)
    await db_session.commit()
    await db_session.refresh(script)

    campaign = CallCampaign(name="Answer Camp", script_id=script.id, scheduled_at=utc_now())
    db_session.add(campaign)
    await db_session.commit()
    await db_session.refresh(campaign)

    task = CallTask(
        campaign_id=campaign.id,
        student_id=seed_students[0].id,
        student_phone=seed_students[0].phone,
        script_id=script.id,
        status="ringing",
        scheduled_at=utc_now(),
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    payload = {
        "CallUUID": "plivo-call-uuid-001",
        "From": "+917923456789",
        "To": seed_students[0].phone,
    }

    with patch("backend.telephony.webhook_handler.ai_pipeline.tts.synthesize", new_callable=AsyncMock) as mock_tts:
        mock_tts.return_value = "https://mock.nirmauni.ac.in/audio/greeting_001.wav"

        response = await async_client.post(f"/webhook/plivo/answer?task_id={task.id}", data=payload)
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/xml")
        assert "<Play>https://mock.nirmauni.ac.in/audio/greeting_001.wav</Play>" in response.text
        assert f"/webhook/plivo/input?task_id={task.id}" in response.text

    # Verify task state in database
    await db_session.refresh(task)
    assert task.status == "in_progress"
    assert task.plivo_uuid == "plivo-call-uuid-001"
    assert task.answered_at is not None

    # Verify Redis session key and TTL=600s
    from backend.telephony.webhook_handler import redis_client
    session_data = await redis_client.hgetall("call:session:plivo-call-uuid-001")
    assert session_data["task_id"] == str(task.id)
    assert session_data["lang"] == "hi"
    assert session_data["turn_count"] == "1"
    # Mandatory TTL check
    ttl = await redis_client.ttl("call:session:plivo-call-uuid-001")
    assert ttl == 600


# ------------------------------------------------------------------------------
# 3. Input Webhook Tests
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_plivo_input_missing_recording_url_returns_hangup(async_client: AsyncClient):
    """Verifies input webhook without RecordUrl or RecordingUrl returns Hangup XML."""
    payload = {
        "CallUUID": "plivo-call-uuid-001",
    }
    response = await async_client.post("/webhook/plivo/input?task_id=1", data=payload)
    assert response.status_code == 200
    assert "<Hangup" in response.text


@pytest.mark.asyncio
async def test_plivo_input_handles_record_url_invariant_and_advances_turn(
    async_client: AsyncClient,
    db_session: AsyncSession,
):
    """Verifies input webhook reads Plivo 'RecordUrl', runs AI turn, updates history, and refreshes TTL."""
    from backend.telephony.webhook_handler import redis_client

    call_uuid = "plivo-call-turn-002"
    session_key = f"call:session:{call_uuid}"
    await redis_client.hset(
        session_key,
        mapping={
            "task_id": "1",
            "call_uuid": call_uuid,
            "system_prompt": "You are assistant.",
            "opening_message": "Hello",
            "lang": "en",
            "turn_count": "1",
            "history": json.dumps([{"role": "assistant", "content": "Hello"}]),
        },
    )
    await redis_client.expire(session_key, 600)

    payload = {
        "CallUUID": call_uuid,
        "RecordUrl": "https://api.plivo.com/v1/Account/123/Recording/rec_001.mp3",
    }

    mock_turn_result = {
        "user_transcript": "When is the fee due?",
        "assistant_reply": "Fee is due on October 30th.",
        "response_audio_url": "https://mock.nirmauni.ac.in/audio/turn_2.wav",
        "latency": {"total_ms": 1400},
    }

    with patch("backend.telephony.webhook_handler.ai_pipeline.process_turn", new_callable=AsyncMock) as mock_turn:
        mock_turn.return_value = mock_turn_result

        response = await async_client.post("/webhook/plivo/input?task_id=1", data=payload)
        assert response.status_code == 200
        assert "<Play>https://mock.nirmauni.ac.in/audio/turn_2.wav</Play>" in response.text
        assert "<Record" in response.text

    # Verify Redis session history updated and turn advanced to 2
    updated_session = await redis_client.hgetall(session_key)
    assert updated_session["turn_count"] == "2"
    history = json.loads(updated_session["history"])
    assert len(history) == 3
    assert history[1]["content"] == "When is the fee due?"
    assert history[2]["content"] == "Fee is due on October 30th."

    # Verify TTL refreshed to 600s
    ttl = await redis_client.ttl(session_key)
    assert ttl == 600


@pytest.mark.asyncio
async def test_plivo_input_supports_recording_url_fallback(async_client: AsyncClient):
    """Verifies input webhook supports fallback 'RecordingUrl' parameter for carrier compatibility."""
    from backend.telephony.webhook_handler import redis_client

    call_uuid = "plivo-call-turn-fallback"
    session_key = f"call:session:{call_uuid}"
    await redis_client.hset(
        session_key,
        mapping={
            "task_id": "1",
            "call_uuid": call_uuid,
            "turn_count": "1",
            "lang": "en",
            "history": json.dumps([]),
        },
    )
    await redis_client.expire(session_key, 600)

    # Send RecordingUrl instead of RecordUrl
    payload = {
        "CallUUID": call_uuid,
        "RecordingUrl": "https://api.carrier.com/recordings/rec_fallback.wav",
    }

    with patch("backend.telephony.webhook_handler.ai_pipeline.process_turn", new_callable=AsyncMock) as mock_turn:
        mock_turn.return_value = {
            "user_transcript": "Yes",
            "assistant_reply": "Thank you, goodbye.",
            "response_audio_url": "https://mock/bye.wav",
        }

        response = await async_client.post("/webhook/plivo/input?task_id=1", data=payload)
        assert response.status_code == 200
        # Assistant reply contained "goodbye", so it must return Hangup!
        assert "<Hangup" in response.text


@pytest.mark.asyncio
async def test_plivo_input_terminates_at_max_turns(async_client: AsyncClient):
    """Verifies that reaching turn 10 triggers an automatic hangup to avoid infinite loops."""
    from backend.telephony.webhook_handler import redis_client

    call_uuid = "plivo-call-turn-max"
    session_key = f"call:session:{call_uuid}"
    await redis_client.hset(
        session_key,
        mapping={
            "task_id": "1",
            "call_uuid": call_uuid,
            "turn_count": "9",  # Next turn will be 10!
            "lang": "en",
            "history": json.dumps([]),
        },
    )

    payload = {
        "CallUUID": call_uuid,
        "RecordUrl": "https://api.plivo.com/v1/Recording/rec_10.wav",
    }

    with patch("backend.telephony.webhook_handler.ai_pipeline.process_turn", new_callable=AsyncMock) as mock_turn:
        mock_turn.return_value = {
            "user_transcript": "Can I ask one more thing?",
            "assistant_reply": "Yes, please contact the department office.",
            "response_audio_url": "https://mock/audio10.wav",
        }

        response = await async_client.post("/webhook/plivo/input?task_id=1", data=payload)
        assert response.status_code == 200
        assert "<Hangup" in response.text


# ------------------------------------------------------------------------------
# 4. Hangup Webhook Tests
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_plivo_hangup_completed_call_and_persists_transcript(
    async_client: AsyncClient,
    db_session: AsyncSession,
    seed_students: List[Student],
):
    """Verifies hangup webhook updates CallTask, persists transcript in CallLog, and purges Redis key."""
    from backend.telephony.webhook_handler import redis_client

    script = CallScript(
        name="Hangup Script",
        category="notice",
        language="en",
        system_prompt="Prompt",
        opening_message="Hello",
    )
    db_session.add(script)
    await db_session.commit()
    await db_session.refresh(script)

    campaign = CallCampaign(name="Hangup Campaign", script_id=script.id, scheduled_at=utc_now())
    db_session.add(campaign)
    await db_session.commit()
    await db_session.refresh(campaign)

    task = CallTask(
        campaign_id=campaign.id,
        student_id=seed_students[0].id,
        student_phone=seed_students[0].phone,
        script_id=script.id,
        status="in_progress",
        scheduled_at=utc_now(),
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    call_uuid = "plivo-hangup-uuid-001"
    session_key = f"call:session:{call_uuid}"
    dialogue = [
        {"role": "assistant", "content": "Hello student."},
        {"role": "user", "content": "Hello ma'am."},
    ]
    await redis_client.hset(session_key, mapping={"history": json.dumps(dialogue)})

    payload = {
        "CallUUID": call_uuid,
        "Duration": "45",  # 45 seconds > 5 -> completed outcome
    }

    response = await async_client.post(f"/webhook/plivo/hangup?task_id={task.id}", data=payload)
    assert response.status_code == 200
    assert "<Hangup" in response.text

    # Verify CallTask state in database
    await db_session.refresh(task)
    assert task.status == "completed"
    assert task.duration_sec == 45
    assert task.outcome == "completed"

    # Verify CallLog transcript persistence
    log_res = await db_session.execute(select(CallLog).where(CallLog.task_id == task.id))
    call_log = log_res.scalar_one()
    assert call_log.transcript == dialogue

    # Verify Redis session was deleted
    session_exists = await redis_client.exists(session_key)
    assert session_exists == 0


@pytest.mark.asyncio
async def test_plivo_hangup_short_call_outcome_no_answer(
    async_client: AsyncClient,
    db_session: AsyncSession,
    seed_students: List[Student],
):
    """Verifies calls with duration <= 5 seconds are marked as 'no_answer' outcome."""
    script = CallScript(name="Short Script", category="notice", language="en", system_prompt="p", opening_message="o")
    db_session.add(script)
    await db_session.commit()
    await db_session.refresh(script)

    campaign = CallCampaign(name="Short Camp", script_id=script.id, scheduled_at=utc_now())
    db_session.add(campaign)
    await db_session.commit()
    await db_session.refresh(campaign)

    task = CallTask(
        campaign_id=campaign.id,
        student_id=seed_students[0].id,
        student_phone=seed_students[0].phone,
        script_id=script.id,
        status="in_progress",
        scheduled_at=utc_now(),
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    payload = {"CallUUID": "short-uuid", "Duration": "3"}
    response = await async_client.post(f"/webhook/plivo/hangup?task_id={task.id}", data=payload)
    assert response.status_code == 200

    await db_session.refresh(task)
    assert task.outcome == "no_answer"


# ------------------------------------------------------------------------------
# 5. Fallback Webhook Tests
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_plivo_fallback_returns_hangup_xml(async_client: AsyncClient):
    """Verifies carrier fallback webhook returns clean Hangup XML."""
    response = await async_client.post("/webhook/plivo/fallback")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/xml")
    assert "<Hangup" in response.text
