"""
Telephony Subpackage Exports.
"""

from backend.telephony.adapter import BaseTelephonyAdapter, CallDispatchResult
from backend.telephony.plivo_adapter import PlivoAdapter
from backend.telephony.webhook_handler import router as webhook_router

__all__ = [
    "BaseTelephonyAdapter",
    "CallDispatchResult",
    "PlivoAdapter",
    "webhook_router",
]
