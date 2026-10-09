"""
Concurrency, Distributed Locking & Race Condition Tests.

Tests:
- Concurrent Turn Webhook Deduplication: Prevents double-processing of duplicate carrier webhooks.
- Celery Scheduler Batch Dispatch Lock: Prevents multiple worker processes from dispatching identical batches.
- Campaign Task Generation Deduplication: Idempotent generation prevents duplicate tasks for identical students.
"""

import asyncio
import json
from typing import Dict, List
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from backend.database.models import CallCampaign, CallScript, CallTask, Student, utc_now
from backend.scheduler.campaign_runner import CampaignRunner
from backend.scheduler.tasks import dispatch_due_calls
import backend.telephony.webhook_handler as wh


@pytest.mark.asyncio
async def test_concurrent_turn_webhooks_deduplicated_by_distributed_lock(
    async_client: AsyncClient,
):
    """
    Race Condition: Carrier sends duplicate concurrent webhook requests for the same turn.
    Invariant: Distributed lock allows exactly ONE request through to process the turn;
    competing request receives `<Response/>` without corrupting turn count or duplicating transcript.
    """
    call_uuid = "plivo-concurrent-call-uuid-99"
    session_key = f"call:session:{call_uuid}"

    await wh.redis_client.hset(
        session_key,
        mapping={
            "task_id": "99",
            "call_uuid": call_uuid,
            "turn_count": "1",
            "lang": "en",
            "system_prompt": "You are assistant.",
            "history": json.dumps([{"role": "assistant", "content": "Hello"}]),
        },
    )
    await wh.redis_client.expire(session_key, 600)

    payload = {
        "CallUUID": call_uuid,
        "RecordUrl": "https://api.plivo.com/v1/Recordings/concurrent_turn.mp3",
    }

    turn_mock = {
        "user_transcript": "Concurrent check",
        "assistant_reply": "Got it.",
        "response_audio_url": "https://mock/reply.wav",
        "latency": {"total_ms": 1100},
    }

    # Simulate AI processing delay
    async def slow_process_turn(*args, **kwargs):
        await asyncio.sleep(0.05)
        return turn_mock

    with patch("backend.telephony.webhook_handler.ai_pipeline.process_turn", side_effect=slow_process_turn):
        # Fire 2 parallel requests simultaneously
        req1 = async_client.post("/webhook/plivo/input?task_id=99", data=payload)
        req2 = async_client.post("/webhook/plivo/input?task_id=99", data=payload)

        resp1, resp2 = await asyncio.gather(req1, req2)

        # Both must return HTTP 200 XML
        assert resp1.status_code == 200
        assert resp2.status_code == 200

        # One response must be processed with <Play>, the other must be deduplicated <Response/>
        responses = [resp1.text, resp2.text]
        assert any("<Play>" in r for r in responses)
        assert any("<Response/>" in r or "<Response />" in r for r in responses)

    # Verify state was only updated ONCE (turn_count == 2, NOT 3)
    final_session = await wh.redis_client.hgetall(session_key)
    assert final_session["turn_count"] == "2"
    history = json.loads(final_session["history"])
    # 1 initial + 1 user + 1 assistant = 3 messages (not 5)
    assert len(history) == 3


def test_concurrent_scheduler_dispatch_blocked_by_lock(monkeypatch):
    """
    Concurrency Invariant: When another Celery worker currently holds lock:scheduler:batch_dispatch,
    concurrent execution skips tick safely and dispatches 0 calls.
    """
    monkeypatch.setattr("backend.scheduler.tasks.is_within_trai_calling_window", lambda: True)

    class MockCompetingRedisClient:
        def set(self, key, val, nx=False, ex=None):
            return False  # Competing worker already holds lock

    monkeypatch.setattr("redis.from_url", lambda url, **kwargs: MockCompetingRedisClient())

    dispatched = dispatch_due_calls()
    assert dispatched == 0


def test_campaign_runner_concurrent_execution_idempotency(sync_db_session: Session):
    """
    Concurrency Invariant: Executing task generation twice on the same campaign
    never creates duplicate call tasks for the same student.
    """
    script = CallScript(name="Script", category="notice", language="en", system_prompt="p", opening_message="o")
    sync_db_session.add(script)
    sync_db_session.commit()

    student = Student(roll_number="CONC01", name="Conc Student", phone="+919876540001", is_active=True)
    sync_db_session.add(student)
    sync_db_session.commit()

    campaign = CallCampaign(name="Conc Camp", script_id=script.id, scheduled_at=utc_now())
    sync_db_session.add(campaign)
    sync_db_session.commit()

    count1 = CampaignRunner.generate_tasks_for_campaign(campaign.id, sync_db_session)
    assert count1 == 1

    # Second invocation immediately after
    count2 = CampaignRunner.generate_tasks_for_campaign(campaign.id, sync_db_session)
    assert count2 == 0

    # Verify total task count in database remains strictly 1
    total_tasks = sync_db_session.query(CallTask).filter(CallTask.campaign_id == campaign.id).count()
    assert total_tasks == 1
