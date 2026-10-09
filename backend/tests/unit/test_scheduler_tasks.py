"""
Unit Tests — Celery Background Tasks, TRAI Compliance & Periodic Schedules.

Tests `backend.scheduler.tasks`:
- is_within_trai_calling_window: 09:00 - 21:00 IST regulatory boundary validation.
- dispatch_due_calls: Periodic polling, TRAI guardrails, distributed lock protection.
- place_call_task: Idempotent call placement, status transition to 'ringing', failure retries.
- retry_no_answer_calls: Auto-rescheduling unanswered calls within campaign limits.
- cleanup_old_sessions: Daily purging of static audio cache files older than 30 days.
"""

import datetime
import os
import time
from unittest.mock import MagicMock, patch
import pytest
import pytz
from sqlalchemy.orm import Session

from backend.database.models import CallCampaign, CallScript, CallTask, Student, utc_now
from backend.scheduler.tasks import (
    IST_TIMEZONE,
    cleanup_old_sessions,
    dispatch_due_calls,
    is_within_trai_calling_window,
    place_call_task,
    retry_no_answer_calls,
)


# ------------------------------------------------------------------------------
# TRAI Regulatory Window Tests
# ------------------------------------------------------------------------------
def test_is_within_trai_calling_window_allowed_hours(monkeypatch):
    """Verifies that hours between 09:00 and 21:00 IST return True."""
    fixed_time = datetime.datetime(2026, 10, 15, 14, 30, 0, tzinfo=IST_TIMEZONE)

    class MockDatetime(datetime.datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_time

    monkeypatch.setattr(datetime, "datetime", MockDatetime)
    assert is_within_trai_calling_window() is True


def test_is_within_trai_calling_window_before_9am(monkeypatch):
    """Verifies that calling before 09:00:00 IST is strictly blocked (returns False)."""
    fixed_time = datetime.datetime(2026, 10, 15, 8, 45, 0, tzinfo=IST_TIMEZONE)

    class MockDatetime(datetime.datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_time

    monkeypatch.setattr(datetime, "datetime", MockDatetime)
    assert is_within_trai_calling_window() is False


def test_is_within_trai_calling_window_after_9pm(monkeypatch):
    """Verifies that calling after 21:00:00 IST is strictly blocked (returns False)."""
    fixed_time = datetime.datetime(2026, 10, 15, 21, 15, 0, tzinfo=IST_TIMEZONE)

    class MockDatetime(datetime.datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_time

    monkeypatch.setattr(datetime, "datetime", MockDatetime)
    assert is_within_trai_calling_window() is False


# ------------------------------------------------------------------------------
# Dispatch Due Calls Tests
# ------------------------------------------------------------------------------
def test_dispatch_due_calls_defers_when_outside_trai(monkeypatch):
    """Verifies dispatch_due_calls defers execution and returns 0 when outside TRAI hours."""
    monkeypatch.setattr("backend.scheduler.tasks.is_within_trai_calling_window", lambda: False)
    dispatched = dispatch_due_calls()
    assert dispatched == 0


def test_dispatch_due_calls_skips_when_lock_not_acquired(monkeypatch):
    """Verifies dispatch_due_calls skips tick if another worker process holds the batch lock."""
    monkeypatch.setattr("backend.scheduler.tasks.is_within_trai_calling_window", lambda: True)

    class MockRedisLockClient:
        def set(self, key, val, nx=False, ex=None):
            return False  # Lock acquisition failed (already active)

    monkeypatch.setattr("redis.from_url", lambda url, **kwargs: MockRedisLockClient())
    dispatched = dispatch_due_calls()
    assert dispatched == 0


# ------------------------------------------------------------------------------
# Place Call Task Tests
# ------------------------------------------------------------------------------
def test_place_call_task_skips_nonexistent_task(sync_db_session: Session):
    """Verifies place_call_task returns None for invalid or deleted task IDs."""
    with patch("backend.scheduler.tasks.get_sync_session") as mock_session_ctx:
        mock_session_ctx.return_value.__enter__.return_value = sync_db_session
        result = place_call_task(999999)
        assert result is None


def test_place_call_task_skips_already_completed_task(sync_db_session: Session):
    """Verifies place_call_task skips calls that have already completed or cancelled."""
    # Seed script, student, campaign, task
    script = CallScript(
        name="Test Script",
        category="notice",
        language="en",
        system_prompt="prompt",
        opening_message="hello",
    )
    student = Student(roll_number="21BCE991", name="Test Student", phone="+919876599991")
    sync_db_session.add_all([script, student])
    sync_db_session.commit()

    campaign = CallCampaign(
        name="Campaign",
        script_id=script.id,
        scheduled_at=utc_now(),
    )
    sync_db_session.add(campaign)
    sync_db_session.commit()

    task = CallTask(
        campaign_id=campaign.id,
        student_id=student.id,
        student_phone=student.phone,
        script_id=script.id,
        status="completed",  # Already finished!
        scheduled_at=utc_now(),
    )
    sync_db_session.add(task)
    sync_db_session.commit()

    with patch("backend.scheduler.tasks.get_sync_session") as mock_session_ctx:
        mock_session_ctx.return_value.__enter__.return_value = sync_db_session
        result = place_call_task(task.id)
        assert result is None


def test_place_call_task_successful_dispatch(sync_db_session: Session):
    """Verifies place_call_task dispatches call via adapter and updates task to 'ringing'."""
    script = CallScript(
        name="Dispatch Script",
        category="fee_reminder",
        language="hi",
        system_prompt="fee reminder",
        opening_message="namaste",
    )
    student = Student(roll_number="21BCE992", name="Aarav", phone="+919876599992")
    sync_db_session.add_all([script, student])
    sync_db_session.commit()

    campaign = CallCampaign(
        name="Test Dispatch Campaign",
        script_id=script.id,
        scheduled_at=utc_now(),
    )
    sync_db_session.add(campaign)
    sync_db_session.commit()

    task = CallTask(
        campaign_id=campaign.id,
        student_id=student.id,
        student_phone=student.phone,
        script_id=script.id,
        status="pending",
        scheduled_at=utc_now(),
    )
    sync_db_session.add(task)
    sync_db_session.commit()

    with patch("backend.scheduler.tasks.get_sync_session") as mock_session_ctx:
        mock_session_ctx.return_value.__enter__.return_value = sync_db_session
        with patch.object(
            place_call_task, "retry", side_effect=lambda exc: None
        ):
            call_uuid = place_call_task(task.id)
            assert call_uuid is not None
            assert call_uuid.startswith("mock_")

            # Check database update
            sync_db_session.refresh(task)
            assert task.status == "ringing"
            assert task.plivo_uuid == call_uuid
            assert task.placed_at is not None


# ------------------------------------------------------------------------------
# Retry No Answer Calls Tests
# ------------------------------------------------------------------------------
def test_retry_no_answer_calls_reschedules_eligible_tasks(sync_db_session: Session):
    """Verifies retry_no_answer_calls reschedules tasks when retry_count < max_retries."""
    script = CallScript(
        name="Retry Script",
        category="fee_reminder",
        language="hi",
        system_prompt="fee reminder",
        opening_message="namaste",
    )
    student = Student(roll_number="21BCE993", name="Diya", phone="+919876599993")
    sync_db_session.add_all([script, student])
    sync_db_session.commit()

    campaign = CallCampaign(
        name="Retry Campaign",
        script_id=script.id,
        scheduled_at=utc_now(),
        max_retries=2,
        retry_delay_min=30,
    )
    sync_db_session.add(campaign)
    sync_db_session.commit()

    # Eligible task: outcome='no_answer', retry_count=0
    eligible_task = CallTask(
        campaign_id=campaign.id,
        student_id=student.id,
        student_phone=student.phone,
        script_id=script.id,
        status="completed",
        outcome="no_answer",
        retry_count=0,
        scheduled_at=utc_now(),
    )
    # Ineligible task: outcome='no_answer', retry_count=2 (already at max)
    maxed_task = CallTask(
        campaign_id=campaign.id,
        student_id=student.id,
        student_phone=student.phone,
        script_id=script.id,
        status="completed",
        outcome="no_answer",
        retry_count=2,
        scheduled_at=utc_now(),
    )
    sync_db_session.add_all([eligible_task, maxed_task])
    sync_db_session.commit()

    with patch("backend.scheduler.tasks.get_sync_session") as mock_session_ctx:
        mock_session_ctx.return_value.__enter__.return_value = sync_db_session
        count = retry_no_answer_calls()
        assert count == 1

        sync_db_session.refresh(eligible_task)
        sync_db_session.refresh(maxed_task)

        assert eligible_task.status == "pending"
        assert eligible_task.outcome is None
        assert eligible_task.retry_count == 1

        # Maxed task should remain completed
        assert maxed_task.status == "completed"
        assert maxed_task.retry_count == 2


# ------------------------------------------------------------------------------
# Audio Cache Cleanup Tests
# ------------------------------------------------------------------------------
def test_cleanup_old_sessions_purges_stale_files(tmp_path, monkeypatch):
    """Verifies cleanup_old_sessions deletes files older than 30 days and retains recent files."""
    cache_dir = tmp_path / "audio_cache"
    cache_dir.mkdir()
    monkeypatch.setattr("backend.scheduler.tasks.settings.audio_cache_dir", str(cache_dir))

    # Create stale file (40 days old)
    stale_file = cache_dir / "tts_old.wav"
    stale_file.write_bytes(b"old_audio")
    old_time = time.time() - (40 * 86400)
    os.utime(str(stale_file), (old_time, old_time))

    # Create fresh file (2 days old)
    fresh_file = cache_dir / "tts_recent.wav"
    fresh_file.write_bytes(b"recent_audio")

    deleted_count = cleanup_old_sessions()
    assert deleted_count == 1
    assert not stale_file.exists()
    assert fresh_file.exists()
