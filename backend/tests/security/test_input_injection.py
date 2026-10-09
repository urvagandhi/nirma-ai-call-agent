"""
Adversarial Input Validation & Injection Security Tests.

Tests:
- SQL injection patterns in query parameters and search strings.
- Malformed and corrupt JSON payloads.
- Type confusion and schema validation errors (e.g., string for integer).
- Parameter boundary violations (negative numbers, extreme pagination limits).
- Cross-site scripting (XSS) string persistence safety.
- Unicode, Devanagari, and Gujarati multi-byte character preservation.
- Massive string payload boundary resilience.
"""

from typing import Dict, List
from httpx import AsyncClient
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import CallCampaign, CallScript, Student, utc_now


@pytest.mark.asyncio
async def test_sqli_in_campaign_status_filter_handled_safely(
    async_client: AsyncClient,
    admin_headers: Dict[str, str],
):
    """
    Adversarial Attack: Injecting SQL syntax into query parameter ?status=
    Expected: Cleanly handled via parameterized queries, returns empty items list without 500.
    """
    payload = "pending' OR '1'='1"
    response = await async_client.get(f"/api/campaigns?status={payload}", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 0


@pytest.mark.asyncio
async def test_sqli_in_calls_path_parameter_rejected(
    async_client: AsyncClient,
    admin_headers: Dict[str, str],
):
    """
    Adversarial Attack: Injecting SQL syntax into path parameter /api/calls/{task_id}.
    Expected: Rejected with 422 Unprocessable Entity (strict type validation), zero SQL execution.
    """
    payload = "1' OR '1'='1"
    response = await async_client.get(f"/api/calls/{payload}", headers=admin_headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_malformed_json_body_rejected_with_422(
    async_client: AsyncClient,
    admin_headers: Dict[str, str],
):
    """
    Adversarial Attack: Sending truncated/unclosed JSON string.
    Expected: Rejected with 422 Unprocessable Entity.
    """
    malformed_json = '{"name": "Truncated Campaign", "script_id": '
    headers = {**admin_headers, "Content-Type": "application/json"}
    response = await async_client.post("/api/campaigns", content=malformed_json, headers=headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_type_confusion_string_for_integer_rejected(
    async_client: AsyncClient,
    admin_headers: Dict[str, str],
):
    """
    Adversarial Attack: Passing alphanumeric string for integer script_id.
    Expected: Rejected with 422 validation error.
    """
    body = {
        "name": "Type Confusion Test",
        "script_id": "not-a-number",
    }
    response = await async_client.post("/api/campaigns", json=body, headers=admin_headers)
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("script_id" in str(err.get("loc", [])) for err in errors)


@pytest.mark.asyncio
async def test_pagination_boundary_violations(
    async_client: AsyncClient,
    admin_headers: Dict[str, str],
):
    """
    Boundary Attack: Submitting negative limits or limits exceeding maximum allowed (100).
    Expected: 422 validation rejection.
    """
    # Negative limit
    resp_neg = await async_client.get("/api/campaigns?limit=-5", headers=admin_headers)
    assert resp_neg.status_code == 422

    # Limit = 0 (must be >= 1)
    resp_zero = await async_client.get("/api/campaigns?limit=0", headers=admin_headers)
    assert resp_zero.status_code == 422

    # Limit exceeding max allowed 100
    resp_overflow = await async_client.get("/api/campaigns?limit=101", headers=admin_headers)
    assert resp_overflow.status_code == 422


@pytest.mark.asyncio
async def test_xss_payload_persisted_safely_as_text(
    async_client: AsyncClient,
    admin_headers: Dict[str, str],
    db_session: AsyncSession,
):
    """
    Adversarial Attack: Submitting XSS script tags in campaign name.
    Expected: Successfully saved as raw string without execution or rendering vulnerabilities.
    """
    script = CallScript(
        name="XSS Test Script",
        category="notice",
        language="en",
        system_prompt="Prompt",
        opening_message="Hello",
    )
    db_session.add(script)
    await db_session.commit()
    await db_session.refresh(script)

    xss_name = "<script>alert('XSS_ATTACK_VECTOR')</script>"
    body = {
        "name": xss_name,
        "script_id": script.id,
        "scheduled_at": "2026-10-15T10:00:00Z",
    }
    response = await async_client.post("/api/campaigns", json=body, headers=admin_headers)
    assert response.status_code == 201
    created_camp = response.json()
    assert created_camp["name"] == xss_name

    # Verify database persistence contains raw escaped string
    res = await db_session.execute(select(CallCampaign).where(CallCampaign.id == created_camp["id"]))
    camp = res.scalar_one()
    assert camp.name == xss_name


@pytest.mark.asyncio
async def test_multilingual_unicode_preservation(
    async_client: AsyncClient,
    admin_headers: Dict[str, str],
    db_session: AsyncSession,
):
    """
    Verifies multi-byte Gujarati and Hindi Devanagari Unicode characters are perfectly preserved.
    """
    script = CallScript(
        name="ભાષા સ્ક્રિપ્ટ",
        category="notice",
        language="gu",
        system_prompt="તમે નિર્મા યુનિવર્સિટીના પ્રતિનિધિ છો.",
        opening_message="નમસ્તે, નિર્મા યુનિવર્સિટીમાંથી આપનું સ્વાગત છે.",
    )
    db_session.add(script)
    await db_session.commit()
    await db_session.refresh(script)

    unicode_name = "ફી સ્મૃતિપત્રક ડિસેમ્બર ૨૦૨૬ (फीस अनुस्मारक)"
    body = {
        "name": unicode_name,
        "script_id": script.id,
        "scheduled_at": "2026-10-15T10:00:00Z",
    }
    response = await async_client.post("/api/campaigns", json=body, headers=admin_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == unicode_name
