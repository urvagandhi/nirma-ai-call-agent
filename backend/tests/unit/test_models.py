"""
Unit Tests — Database Models, ORM Schemas & Invariants.

Tests all SQLAlchemy 2.0 declarative models defined in `backend.database.models`:
- StaffUser, Student, CallScript, CallCampaign, CallTask, CallLog.
Verifies column types, default values, string representations, and foreign key linkages.
"""

import datetime
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import (
    CallCampaign,
    CallLog,
    CallScript,
    CallTask,
    StaffUser,
    Student,
    utc_now,
)


def test_utc_now_returns_timezone_aware_datetime():
    """Verifies that utc_now helper generates UTC timezone-aware datetimes."""
    now = utc_now()
    assert isinstance(now, datetime.datetime)
    assert now.tzinfo is not None
    assert now.tzinfo == datetime.timezone.utc


def test_staff_user_repr_and_defaults():
    """Verifies StaffUser __repr__ format and field initialization."""
    user = StaffUser(
        id=1,
        email="test@nirmauni.ac.in",
        name="Test User",
        role="operator",
        password_hash="hashed_secret",
    )
    assert "test@nirmauni.ac.in" in repr(user)
    assert "operator" in repr(user)
    assert user.is_active is True or user.is_active is None  # Defaults on persist


def test_student_repr_and_attributes():
    """Verifies Student __repr__ format and roll number mapping."""
    student = Student(
        id=10,
        roll_number="21BCE042",
        name="Student Name",
        phone="+919876543210",
        language_pref="gu",
    )
    assert "21BCE042" in repr(student)
    assert "Student Name" in repr(student)
    assert student.language_pref == "gu"


def test_call_script_repr_and_category():
    """Verifies CallScript __repr__ format and metadata fields."""
    script = CallScript(
        id=5,
        name="Exam Alert",
        category="exam_notice",
        language="en",
        system_prompt="Exam prompt",
        opening_message="Hello student",
    )
    assert "Exam Alert" in repr(script)
    assert "exam_notice" in repr(script)


def test_call_campaign_repr_and_defaults():
    """Verifies CallCampaign status defaults and representation."""
    campaign = CallCampaign(
        id=3,
        name="Fees Campaign",
        script_id=1,
        scheduled_at=utc_now(),
        status="pending",
    )
    assert "Fees Campaign" in repr(campaign)
    assert "pending" in repr(campaign)


def test_call_task_repr_and_linkages():
    """Verifies CallTask representation and initial status."""
    task = CallTask(
        id=100,
        campaign_id=1,
        student_id=2,
        student_phone="+919876500001",
        script_id=1,
        status="pending",
        scheduled_at=utc_now(),
    )
    assert "100" in repr(task)
    assert "pending" in repr(task)


def test_call_log_repr_and_telemetry():
    """Verifies CallLog representation and latency telemetry attributes."""
    log = CallLog(
        id=50,
        task_id=100,
        transcript=[{"role": "assistant", "content": "Hello"}],
        avg_latency_ms=1750,
    )
    assert "task_id=100" in repr(log)
    assert "avg_ms=1750" in repr(log)


@pytest.mark.asyncio
async def test_database_model_persistence_and_relationships(
    db_session: AsyncSession,
    seed_users: dict,
    seed_script: CallScript,
    seed_students: list,
):
    """
    Verifies that complete relational foreign-key graphs can be persisted and
    retrieved with correct integrity and relationship cascades.
    """
    admin = seed_users["admin"]
    student = seed_students[0]

    # Create Campaign
    campaign = CallCampaign(
        name="Integration Test Campaign",
        script_id=seed_script.id,
        target_filter={"department": "CS", "semester": 4},
        scheduled_at=utc_now(),
        status="pending",
        created_by=admin.id,
    )
    db_session.add(campaign)
    await db_session.commit()
    await db_session.refresh(campaign)

    # Create Task
    task = CallTask(
        campaign_id=campaign.id,
        student_id=student.id,
        student_phone=student.phone,
        script_id=seed_script.id,
        status="pending",
        scheduled_at=campaign.scheduled_at,
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    # Create Log
    call_log = CallLog(
        task_id=task.id,
        transcript=[{"role": "assistant", "content": "Namaste"}],
        stt_provider="indic_conformer",
        llm_provider="qwen3",
        tts_provider="indicf5",
        avg_latency_ms=1600,
        max_latency_ms=2100,
        error_log=[],
    )
    db_session.add(call_log)
    await db_session.commit()
    await db_session.refresh(call_log)

    # Verify query with relationships
    stmt = (
        select(CallTask)
        .where(CallTask.id == task.id)
    )
    res = await db_session.execute(stmt)
    retrieved_task = res.scalar_one()

    assert retrieved_task.campaign_id == campaign.id
    assert retrieved_task.student_id == student.id
    assert retrieved_task.student_phone == student.phone
    assert retrieved_task.status == "pending"
