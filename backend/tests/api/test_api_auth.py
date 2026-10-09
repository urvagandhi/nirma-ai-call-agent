"""
API Contract Tests — Authentication Endpoints & Token Lifecycles.

Tests `/auth/*`:
- POST /auth/login: Credential verification, account status checks, JWT token issuance.
- POST /auth/refresh: Refresh token validation, token type discrimination, re-issuance.
- GET /auth/me: Protected profile endpoint, authentication token validation.
"""

from datetime import timedelta
import pytest
from httpx import AsyncClient

from backend.api.auth import create_jwt_token


@pytest.mark.asyncio
async def test_login_success_admin(async_client: AsyncClient, seed_users: dict):
    """Verifies that valid admin credentials return JWT token pair and role information."""
    payload = {
        "email": "admin@nirmauni.ac.in",
        "password": "NirmaPassword123!",
    }
    response = await async_client.post("/auth/login", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "admin"
    assert data["name"] == "Admin Coordinator"


@pytest.mark.asyncio
async def test_login_success_operator(async_client: AsyncClient, seed_users: dict):
    """Verifies that valid operator credentials return operator role."""
    payload = {
        "email": "operator@nirmauni.ac.in",
        "password": "NirmaPassword123!",
    }
    response = await async_client.post("/auth/login", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["role"] == "operator"
    assert data["name"] == "Operator Specialist"


@pytest.mark.asyncio
async def test_login_failure_incorrect_password(async_client: AsyncClient, seed_users: dict):
    """Verifies that an incorrect password yields HTTP 401 Unauthorized."""
    payload = {
        "email": "admin@nirmauni.ac.in",
        "password": "WrongPassword123",
    }
    response = await async_client.post("/auth/login", json=payload)
    assert response.status_code == 401
    assert "incorrect email or password" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_failure_unknown_email(async_client: AsyncClient, seed_users: dict):
    """Verifies that an unrecognized email yields HTTP 401 Unauthorized."""
    payload = {
        "email": "ghost@nirmauni.ac.in",
        "password": "NirmaPassword123!",
    }
    response = await async_client.post("/auth/login", json=payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_failure_inactive_account(async_client: AsyncClient, seed_users: dict):
    """Verifies that an inactive user account is rejected with HTTP 403 Forbidden."""
    payload = {
        "email": "inactive@nirmauni.ac.in",
        "password": "NirmaPassword123!",
    }
    response = await async_client.post("/auth/login", json=payload)
    assert response.status_code == 403
    assert "disabled" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_validation_invalid_email_format(async_client: AsyncClient):
    """Verifies that an invalid email format yields HTTP 422 Unprocessable Entity."""
    payload = {
        "email": "not-an-email-address",
        "password": "NirmaPassword123!",
    }
    response = await async_client.post("/auth/login", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_validation_short_password(async_client: AsyncClient):
    """Verifies that passwords under 6 characters yield HTTP 422."""
    payload = {
        "email": "admin@nirmauni.ac.in",
        "password": "123",
    }
    response = await async_client.post("/auth/login", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_refresh_token_success(async_client: AsyncClient, seed_users: dict):
    """Verifies that a valid refresh token produces a new access token."""
    admin = seed_users["admin"]
    valid_refresh = create_jwt_token(
        data={"sub": str(admin.id), "type": "refresh"},
        expires_delta=timedelta(days=7),
    )

    response = await async_client.post("/auth/refresh", json={"refresh_token": valid_refresh})
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert data["role"] == "admin"


@pytest.mark.asyncio
async def test_refresh_token_rejects_access_token(async_client: AsyncClient, seed_users: dict):
    """
    Verifies that passing an access token (missing type='refresh') to /auth/refresh
    is rejected with HTTP 400 Bad Request.
    """
    admin = seed_users["admin"]
    access_token = create_jwt_token(
        data={"sub": str(admin.id), "role": admin.role},
        expires_delta=timedelta(minutes=15),
    )

    response = await async_client.post("/auth/refresh", json={"refresh_token": access_token})
    assert response.status_code == 400
    assert "invalid token type" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_refresh_token_rejects_tampered_token(async_client: AsyncClient):
    """Verifies that a corrupted or altered refresh token returns HTTP 401."""
    response = await async_client.post("/auth/refresh", json={"refresh_token": "tampered.jwt.payload"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_success(async_client: AsyncClient, admin_headers: dict, seed_users: dict):
    """Verifies GET /auth/me returns the authenticated user's profile."""
    response = await async_client.get("/auth/me", headers=admin_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["email"] == "admin@nirmauni.ac.in"
    assert data["role"] == "admin"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_get_me_unauthenticated(async_client: AsyncClient):
    """Verifies GET /auth/me returns HTTP 401 Unauthorized when Authorization header is absent."""
    response = await async_client.get("/auth/me")
    assert response.status_code == 401
