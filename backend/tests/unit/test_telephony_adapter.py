"""
Unit Tests — Telephony Adapter, Plivo PSTN Gateway & Carrier Contracts.

Tests `backend.telephony.adapter` and `backend.telephony.plivo_adapter`:
- BaseTelephonyAdapter abstract interface and default contracts.
- PlivoAdapter synchronous worker dispatch (`place_call_sync`).
- PlivoAdapter asynchronous event-loop threadpool dispatch (`place_call`).
- Local development sandbox / mock UUID generation and fallback simulation.
- Hangup call execution and carrier status polling.
"""

import pytest
from backend.telephony.adapter import BaseTelephonyAdapter, CallDispatchResult
from backend.telephony.plivo_adapter import PlivoAdapter


class IncompleteAdapter(BaseTelephonyAdapter):
    """Concrete adapter omitting place_call_sync implementation for interface testing."""

    async def place_call(self, to_number, answer_url, hangup_url, caller_id):
        return CallDispatchResult(call_uuid="test", status="queued")

    async def hangup_call(self, call_uuid):
        return True

    async def get_call_status(self, call_uuid):
        return "completed"


def test_base_adapter_cannot_be_instantiated_directly():
    """Verifies that BaseTelephonyAdapter is an abstract class with enforced methods."""
    with pytest.raises(TypeError):
        BaseTelephonyAdapter()  # type: ignore


def test_base_adapter_place_call_sync_raises_not_implemented():
    """Verifies that the default place_call_sync raises NotImplementedError unless overridden."""
    adapter = IncompleteAdapter()
    with pytest.raises(NotImplementedError):
        adapter.place_call_sync("+919876500000", "http://a", "http://h", "+919876599999")


def test_plivo_adapter_mock_sandbox_sync():
    """Verifies PlivoAdapter executes direct synchronous mock dispatch in sandbox mode."""
    adapter = PlivoAdapter(auth_id="mock", auth_token="mock")
    res = adapter.place_call_sync(
        to_number="+919876543210",
        answer_url="https://calls.nirmauni.ac.in/webhook/plivo/answer?task_id=1",
        hangup_url="https://calls.nirmauni.ac.in/webhook/plivo/hangup?task_id=1",
        caller_id="+917971600000",
    )
    assert res.status == "queued"
    assert res.call_uuid.startswith("mock_")
    assert res.error is None


@pytest.mark.asyncio
async def test_plivo_adapter_mock_sandbox_async():
    """Verifies PlivoAdapter executes asynchronous mock dispatch via threadpool without blocking."""
    adapter = PlivoAdapter(auth_id="mock", auth_token="mock")
    res = await adapter.place_call(
        to_number="+919876543210",
        answer_url="https://calls.nirmauni.ac.in/webhook/plivo/answer?task_id=1",
        hangup_url="https://calls.nirmauni.ac.in/webhook/plivo/hangup?task_id=1",
        caller_id="+917971600000",
    )
    assert res.status == "queued"
    assert res.call_uuid.startswith("mock_")
    assert res.error is None


@pytest.mark.asyncio
async def test_plivo_adapter_hangup_mock_call():
    """Verifies PlivoAdapter hangup_call terminates mock call and returns True."""
    adapter = PlivoAdapter(auth_id="mock", auth_token="mock")
    res = await adapter.hangup_call(call_uuid="mock_123456789abc")
    assert res is True


@pytest.mark.asyncio
async def test_plivo_adapter_get_call_status_mock():
    """Verifies PlivoAdapter get_call_status returns in-progress for mock call."""
    adapter = PlivoAdapter(auth_id="mock", auth_token="mock")
    status_str = await adapter.get_call_status(call_uuid="mock_123456789abc")
    assert status_str == "in-progress"


def test_plivo_adapter_handles_carrier_failure_gracefully(monkeypatch):
    """Verifies PlivoAdapter catches carrier client exceptions and returns failed CallDispatchResult."""
    adapter = PlivoAdapter(auth_id="REAL_AUTH_ID_INVALID", auth_token="REAL_AUTH_TOKEN_INVALID")

    class MockFailingCalls:
        def create(self, **kwargs):
            raise RuntimeError("Authentication failed with Plivo carrier gateway (401)")

    class MockFailingClient:
        calls = MockFailingCalls()

    monkeypatch.setattr(adapter, "_get_client", lambda: MockFailingClient())

    res = adapter.place_call_sync(
        to_number="+919876543210",
        answer_url="http://ans",
        hangup_url="http://hang",
        caller_id="+917971600000",
    )
    assert res.status == "failed"
    assert "Authentication failed" in (res.error or "")
    assert res.call_uuid == ""
