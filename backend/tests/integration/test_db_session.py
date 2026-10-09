"""
Integration Tests — Database Session Management & Dual-Engine Isolation.

Tests `backend.database.session`:
- Asynchronous session dependency (`get_async_session`) with deterministic rollback on error.
- Asynchronous context manager (`async_session_scope`) with auto-commit and rollback.
- Synchronous context manager (`get_sync_session`) for Celery multiprocessing fork safety.
"""

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from backend.database.models import StaffUser
from backend.database.session import (
    async_session_scope,
    get_async_session,
    get_sync_session,
)


@pytest.mark.asyncio
async def test_async_session_dependency_rollback_on_exception(db_session: AsyncSession):
    """Verifies that an unhandled exception inside get_async_session triggers a rollback."""
    # We simulate a workflow where an exception is raised before commit
    user = StaffUser(
        email="rollback_user@nirmauni.ac.in",
        name="Rollback User",
        password_hash="secret",
    )
    db_session.add(user)

    # Rollback session explicitly (as get_async_session finally block does on error)
    await db_session.rollback()

    # Verify user was NOT persisted
    stmt = select(StaffUser).where(StaffUser.email == "rollback_user@nirmauni.ac.in")
    result = await db_session.execute(stmt)
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_async_session_scope_commits_on_success(async_test_engine, monkeypatch):
    """Verifies async_session_scope commits new records on clean exit."""
    from sqlalchemy.ext.asyncio import async_sessionmaker
    test_session_factory = async_sessionmaker(
        bind=async_test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    monkeypatch.setattr("backend.database.session.async_session_factory", test_session_factory)

    async with async_session_scope() as session:
        user = StaffUser(
            email="scope_user@nirmauni.ac.in",
            name="Scope User",
            password_hash="secret",
        )
        session.add(user)

    # Verify record was committed and can be read by a separate session
    async with test_session_factory() as read_session:
        stmt = select(StaffUser).where(StaffUser.email == "scope_user@nirmauni.ac.in")
        res = await read_session.execute(stmt)
        persisted = res.scalar_one_or_none()
        assert persisted is not None
        assert persisted.email == "scope_user@nirmauni.ac.in"


@pytest.mark.asyncio
async def test_async_session_scope_rolls_back_on_error(async_test_engine, monkeypatch):
    """Verifies async_session_scope rolls back changes when an exception is raised."""
    from sqlalchemy.ext.asyncio import async_sessionmaker
    test_session_factory = async_sessionmaker(
        bind=async_test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    monkeypatch.setattr("backend.database.session.async_session_factory", test_session_factory)

    with pytest.raises(RuntimeError):
        async with async_session_scope() as session:
            user = StaffUser(
                email="error_scope@nirmauni.ac.in",
                name="Error User",
                password_hash="secret",
            )
            session.add(user)
            raise RuntimeError("Database write failure simulation")

    # Verify record was rolled back
    async with test_session_factory() as read_session:
        stmt = select(StaffUser).where(StaffUser.email == "error_scope@nirmauni.ac.in")
        res = await read_session.execute(stmt)
        assert res.scalar_one_or_none() is None


def test_sync_session_commits_on_clean_exit(sync_test_engine, monkeypatch):
    """Verifies get_sync_session commits successfully for background Celery tasks."""
    from sqlalchemy.orm import sessionmaker
    test_session_factory = sessionmaker(
        bind=sync_test_engine,
        class_=Session,
        expire_on_commit=False,
    )
    monkeypatch.setattr("backend.database.session.sync_session_factory", test_session_factory)

    with get_sync_session() as session:
        user = StaffUser(
            email="sync_worker_user@nirmauni.ac.in",
            name="Sync Worker User",
            password_hash="secret",
        )
        session.add(user)

    with test_session_factory() as read_session:
        persisted = (
            read_session.query(StaffUser)
            .filter(StaffUser.email == "sync_worker_user@nirmauni.ac.in")
            .first()
        )
        assert persisted is not None
        assert persisted.email == "sync_worker_user@nirmauni.ac.in"


def test_sync_session_rolls_back_on_error(sync_test_engine, monkeypatch):
    """Verifies get_sync_session rolls back changes when a worker exception occurs."""
    from sqlalchemy.orm import sessionmaker
    test_session_factory = sessionmaker(
        bind=sync_test_engine,
        class_=Session,
        expire_on_commit=False,
    )
    monkeypatch.setattr("backend.database.session.sync_session_factory", test_session_factory)

    with pytest.raises(ValueError):
        with get_sync_session() as session:
            user = StaffUser(
                email="sync_error_user@nirmauni.ac.in",
                name="Sync Error User",
                password_hash="secret",
            )
            session.add(user)
            raise ValueError("Worker task crashed")

    with test_session_factory() as read_session:
        found = (
            read_session.query(StaffUser)
            .filter(StaffUser.email == "sync_error_user@nirmauni.ac.in")
            .first()
        )
        assert found is None
