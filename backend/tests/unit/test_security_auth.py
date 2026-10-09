"""
Unit Tests — Authentication, Password Hashing, JWT Cryptography & Access Control.

Tests all security functions and FastAPI security dependencies in `backend.api.auth`:
- verify_password, get_password_hash
- create_jwt_token
- get_current_user
- require_admin
"""

from datetime import datetime, timedelta, timezone
import pytest
from fastapi import HTTPException, status
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import (
    create_jwt_token,
    get_current_user,
    get_password_hash,
    require_admin,
    verify_password,
)
from backend.config import settings
from backend.database.models import StaffUser


def test_password_hash_and_verification():
    """Verifies that bcrypt hashing creates unique salted hashes and verifies correctly."""
    plain = "SuperSecretPassword123"
    hashed = get_password_hash(plain)

    assert hashed != plain
    assert hashed.startswith("$2b$")
    assert verify_password(plain, hashed) is True
    assert verify_password("WrongPassword123", hashed) is False


def test_jwt_token_creation_and_payload_claims():
    """Verifies that create_jwt_token sets correct subject, custom claims, and expiration."""
    delta = timedelta(minutes=15)
    token = create_jwt_token(data={"sub": "123", "role": "admin"}, expires_delta=delta)

    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    assert payload["sub"] == "123"
    assert payload["role"] == "admin"
    assert "exp" in payload
    # Expiration is in the future
    assert payload["exp"] > datetime.now(timezone.utc).timestamp()


def test_jwt_token_expiration_fails_decoding():
    """Verifies that expired JWT tokens raise ExpiredSignatureError upon decoding."""
    negative_delta = timedelta(minutes=-10)
    token = create_jwt_token(data={"sub": "123"}, expires_delta=negative_delta)

    with pytest.raises(jwt.ExpiredSignatureError):
        jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


def test_jwt_token_tampered_signature_fails():
    """Verifies that cryptographic signature tampering is rejected."""
    token = create_jwt_token(data={"sub": "123"}, expires_delta=timedelta(minutes=10))
    # Alter the last character of the signature
    tampered_token = token[:-4] + "AAAA"

    with pytest.raises(jwt.JWTError):
        jwt.decode(tampered_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


def test_jwt_token_wrong_secret_key_fails():
    """Verifies that tokens signed with an unauthorized secret key are rejected."""
    token = create_jwt_token(data={"sub": "123"}, expires_delta=timedelta(minutes=10))

    with pytest.raises(jwt.JWTError):
        jwt.decode(token, "wrong-unauthorized-secret-key-32-chars", algorithms=[settings.jwt_algorithm])


@pytest.mark.asyncio
async def test_get_current_user_valid(db_session: AsyncSession, seed_users: dict):
    """Verifies get_current_user resolves active StaffUser from valid token."""
    admin = seed_users["admin"]
    token = create_jwt_token(data={"sub": str(admin.id)}, expires_delta=timedelta(minutes=30))

    user = await get_current_user(token=token, session=db_session)
    assert user.id == admin.id
    assert user.email == admin.email


@pytest.mark.asyncio
async def test_get_current_user_inactive_raises_401(db_session: AsyncSession, seed_users: dict):
    """Verifies get_current_user rejects inactive/disabled accounts with HTTP 401."""
    inactive = seed_users["inactive"]
    token = create_jwt_token(data={"sub": str(inactive.id)}, expires_delta=timedelta(minutes=30))

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token=token, session=db_session)
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_current_user_nonexistent_user_raises_401(db_session: AsyncSession):
    """Verifies get_current_user rejects token with non-existent database ID."""
    token = create_jwt_token(data={"sub": "999999"}, expires_delta=timedelta(minutes=30))

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token=token, session=db_session)
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_current_user_invalid_sub_format_raises_401(db_session: AsyncSession):
    """Verifies get_current_user rejects token where 'sub' is not a valid integer string."""
    token = create_jwt_token(data={"sub": "not_an_integer"}, expires_delta=timedelta(minutes=30))

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token=token, session=db_session)
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_current_user_missing_sub_raises_401(db_session: AsyncSession):
    """Verifies get_current_user rejects token where 'sub' claim is absent."""
    token = create_jwt_token(data={"role": "admin"}, expires_delta=timedelta(minutes=30))

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token=token, session=db_session)
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_require_admin_allows_admin(seed_users: dict):
    """Verifies require_admin grants access when user role is 'admin'."""
    admin = seed_users["admin"]
    result = await require_admin(current_user=admin)
    assert result == admin


@pytest.mark.asyncio
async def test_require_admin_blocks_operator_with_403(seed_users: dict):
    """Verifies require_admin raises HTTP 403 Forbidden when user role is 'operator'."""
    operator = seed_users["operator"]
    with pytest.raises(HTTPException) as exc_info:
        await require_admin(current_user=operator)
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert "administrator" in exc_info.value.detail.lower()
